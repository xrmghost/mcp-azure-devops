import os
import asyncio
import logging
import sys
from typing import Any, Dict, List, Optional
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from .azure_devops_client import AzureDevOpsClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger(__name__)

class MCPAzureDevOpsServer:
    """MCP Server for Azure DevOps integration with improved reliability and debugging."""
    
    def __init__(self):
        self.server = Server(name="mcp-azure-devops", version="0.1.0")
        self.client = None
        self.tools_registered = False
        self._setup_tools()
        self._setup_handlers()
        
    def _validate_environment(self) -> bool:
        """Validate required environment variables are set."""
        required_vars = ["AZURE_DEVOPS_ORG_URL", "AZURE_DEVOPS_PAT"]
        missing_vars = []
        
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
            return False
            
        logger.info("Environment validation passed")
        return True
    
    def _initialize_client(self) -> bool:
        """Initialize the Azure DevOps client with error handling."""
        try:
            self.client = AzureDevOpsClient()
            logger.info("Azure DevOps client initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Azure DevOps client: {e}")
            return False
    
    def _setup_tools(self):
        """Define all available tools with comprehensive schemas."""
        self.tools = [
            types.Tool(
                name="create_work_item",
                description="Creates a new work item in Azure DevOps. Supports Epic, User Story, Task, Bug, and work item linking.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                        "work_item_type": {
                            "type": "string", 
                            "description": "The type of work item (e.g., 'Bug', 'User Story', 'Task', 'Epic')."
                        },
                        "title": {
                            "type": "string", 
                            "description": "The title of the work item."
                        },
                        "description": {
                            "type": "string", 
                            "description": "The description of the work item."
                        },
                        "custom_fields": {
                            "type": "object",
                            "description": "A dictionary of custom fields to set on the work item."
                        },
                        "relations": {
                            "type": "array",
                            "description": "A list of relations to other work items.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "rel": {
                                        "type": "string", 
                                        "description": "The relation type (e.g., 'System.LinkTypes.Dependency-Forward')."
                                    },
                                    "url": {
                                        "type": "string", 
                                        "description": "The URL of the related work item."
                                    }
                                },
                                "required": ["rel", "url"]
                            }
                        }
                    },
                    "required": ["project", "work_item_type", "title", "description"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="get_work_item",
                description="Gets a work item by its ID with optional field expansion.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "integer", 
                            "description": "The ID of the work item."
                        },
                        "expand": {
                            "type": "string", 
                            "description": "The expand option for the work item. Use 'All' to get all fields."
                        },
                    },
                    "required": ["work_item_id"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="update_work_item",
                description="Updates a work item by its ID with field changes and relation management.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "integer", 
                            "description": "The ID of the work item to update."
                        },
                        "updates": {
                            "type": "object", 
                            "description": "A dictionary of fields to update."
                        },
                        "relations": {
                            "type": "array",
                            "description": "A list of relations to other work items.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "rel": {
                                        "type": "string", 
                                        "description": "The relation type (e.g., 'System.LinkTypes.Dependency-Forward')."
                                    },
                                    "url": {
                                        "type": "string", 
                                        "description": "The URL of the related work item."
                                    }
                                },
                                "required": ["rel", "url"]
                            }
                        }
                    },
                    "required": ["work_item_id", "updates"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="delete_work_item",
                description="Deletes a work item by its ID.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "integer", 
                            "description": "The ID of the work item to delete."
                        },
                    },
                    "required": ["work_item_id"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="search_work_items",
                description="Searches for work items using a WIQL (Work Item Query Language) query.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                        "wiql_query": {
                            "type": "string", 
                            "description": "The Work Item Query Language (WIQL) query."
                        },
                    },
                    "required": ["project", "wiql_query"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="get_work_item_comments",
                description="Gets comments for a specific work item with pagination support.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "work_item_id": {
                            "type": "integer", 
                            "description": "The ID of the work item to get comments for."
                        },
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project (optional if project context is set)."
                        },
                        "top": {
                            "type": "integer", 
                            "description": "Maximum number of comments to return (for pagination)."
                        },
                        "continuation_token": {
                            "type": "string", 
                            "description": "Token for getting the next page of results."
                        },
                        "include_deleted": {
                            "type": "boolean", 
                            "description": "Whether to include deleted comments (default: false)."
                        },
                        "expand": {
                            "type": "string", 
                            "description": "Additional data retrieval options for work item comments."
                        },
                        "order": {
                            "type": "string", 
                            "description": "Order in which comments should be returned (e.g., 'created_date_asc', 'created_date_desc')."
                        }
                    },
                    "required": ["work_item_id"],
                    "additionalProperties": False
                }
            ),
            # Work Item Metadata Discovery Tools
            types.Tool(
                name="get_work_item_types",
                description="Get all work item types available in a project to help with smart work item management.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                    },
                    "required": ["project"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="get_work_item_states",
                description="Get all possible states for a specific work item type to help with accurate status updates.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                        "work_item_type": {
                            "type": "string", 
                            "description": "The work item type to get states for (e.g., 'Bug', 'User Story', 'Task')."
                        },
                    },
                    "required": ["project", "work_item_type"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="get_work_item_fields",
                description="Get all work item fields available in a project with metadata for smart field updates.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                    },
                    "required": ["project"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="get_work_item_transitions",
                description="Get valid state transitions for a work item type from a specific state to ensure proper workflow.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                        "work_item_type": {
                            "type": "string", 
                            "description": "The work item type (e.g., 'Bug', 'User Story', 'Task')."
                        },
                        "from_state": {
                            "type": "string", 
                            "description": "The current state to get valid transitions from."
                        },
                    },
                    "required": ["project", "work_item_type", "from_state"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="create_wiki_page",
                description="Creates a new wiki page with specified content.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                        "wiki_identifier": {
                            "type": "string", 
                            "description": "The name or ID of the wiki."
                        },
                        "path": {
                            "type": "string", 
                            "description": "The path of the wiki page."
                        },
                        "content": {
                            "type": "string", 
                            "description": "The content of the wiki page."
                        },
                    },
                    "required": ["project", "wiki_identifier", "path", "content"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="get_wiki_page",
                description="Gets a wiki page by its path.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                        "wiki_identifier": {
                            "type": "string", 
                            "description": "The name or ID of the wiki."
                        },
                        "path": {
                            "type": "string", 
                            "description": "The path of the wiki page."
                        },
                    },
                    "required": ["project", "wiki_identifier", "path"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="update_wiki_page",
                description="Updates an existing wiki page with new content.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                        "wiki_identifier": {
                            "type": "string", 
                            "description": "The name or ID of the wiki."
                        },
                        "path": {
                            "type": "string", 
                            "description": "The path of the wiki page."
                        },
                        "content": {
                            "type": "string", 
                            "description": "The content of the wiki page."
                        },
                    },
                    "required": ["project", "wiki_identifier", "path", "content"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="delete_wiki_page",
                description="Deletes a wiki page by its path.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                        "wiki_identifier": {
                            "type": "string", 
                            "description": "The name or ID of the wiki."
                        },
                        "path": {
                            "type": "string", 
                            "description": "The path of the wiki page to delete."
                        },
                    },
                    "required": ["project", "wiki_identifier", "path"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="list_wiki_pages",
                description="Lists all pages in a wiki.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                        "wiki_identifier": {
                            "type": "string", 
                            "description": "The name or ID of the wiki."
                        },
                    },
                    "required": ["project", "wiki_identifier"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="get_wikis",
                description="Gets all wikis in a project.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                    },
                    "required": ["project"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="create_wiki",
                description="Creates a new wiki in a project.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                        "name": {
                            "type": "string", 
                            "description": "The name of the wiki to create."
                        },
                    },
                    "required": ["project", "name"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="list_repositories",
                description="Lists all repositories in a project.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                    },
                    "required": ["project"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="list_files",
                description="Lists files in a repository at a specified path.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                        "repository_id": {
                            "type": "string", 
                            "description": "The name or ID of the repository."
                        },
                        "path": {
                            "type": "string", 
                            "description": "The path to list files from."
                        },
                    },
                    "required": ["project", "repository_id", "path"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="get_file_content",
                description="Gets the content of a file in a repository.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                        "repository_id": {
                            "type": "string", 
                            "description": "The name or ID of the repository."
                        },
                        "path": {
                            "type": "string", 
                            "description": "The path to the file."
                        },
                    },
                    "required": ["project", "repository_id", "path"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="set_project_context",
                description="Sets the project context for subsequent commands to avoid repeating project parameter.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project to set as context."
                        },
                    },
                    "required": ["project"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="clear_project_context",
                description="Clears the project context, reverting to organization-level scope.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="get_projects",
                description="Gets a list of all projects in the organization.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="list_tools",
                description="Lists all available tools with their names.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="get_tool_documentation",
                description="Gets detailed documentation for a specific tool including parameters and examples.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "tool_name": {
                            "type": "string", 
                            "description": "The name of the tool to get documentation for."
                        },
                    },
                    "required": ["tool_name"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="server_health_check",
                description="Performs a comprehensive health check of the server and Azure DevOps connection.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            ),
            # Enhanced Wiki Helper Methods
            types.Tool(
                name="update_wiki_page_safe",
                description="Safely updates a wiki page with automatic retry on version conflicts.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                        "wiki_identifier": {
                            "type": "string", 
                            "description": "The name or ID of the wiki."
                        },
                        "path": {
                            "type": "string", 
                            "description": "The path of the wiki page."
                        },
                        "content": {
                            "type": "string", 
                            "description": "The content of the wiki page."
                        },
                        "max_retries": {
                            "type": "integer", 
                            "description": "Maximum number of retry attempts (default: 3)."
                        },
                    },
                    "required": ["project", "wiki_identifier", "path", "content"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="create_or_update_wiki_page_smart",
                description="Creates a new wiki page or updates existing one intelligently.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                        "wiki_identifier": {
                            "type": "string", 
                            "description": "The name or ID of the wiki."
                        },
                        "path": {
                            "type": "string", 
                            "description": "The path of the wiki page."
                        },
                        "content": {
                            "type": "string", 
                            "description": "The content of the wiki page."
                        },
                    },
                    "required": ["project", "wiki_identifier", "path", "content"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="search_wiki_pages",
                description="Search for wiki pages by title or content.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                        "wiki_identifier": {
                            "type": "string", 
                            "description": "The name or ID of the wiki."
                        },
                        "search_term": {
                            "type": "string", 
                            "description": "The term to search for in page titles and content."
                        },
                    },
                    "required": ["project", "wiki_identifier", "search_term"],
                    "additionalProperties": False
                }
            ),
            # Additional Wiki Navigation Helper Tools
            types.Tool(
                name="get_wiki_page_tree",
                description="Get hierarchical structure of wiki pages for better navigation.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                        "wiki_identifier": {
                            "type": "string", 
                            "description": "The name or ID of the wiki."
                        },
                    },
                    "required": ["project", "wiki_identifier"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="find_wiki_by_name",
                description="Find wikis by partial name match when you don't know the exact wiki name.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                        "partial_name": {
                            "type": "string", 
                            "description": "Partial wiki name to search for."
                        },
                    },
                    "required": ["project", "partial_name"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="get_wiki_page_by_title",
                description="Find a wiki page by title instead of exact path - useful for navigation.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                        "wiki_identifier": {
                            "type": "string", 
                            "description": "The name or ID of the wiki."
                        },
                        "title": {
                            "type": "string", 
                            "description": "Title or partial title of the page to find."
                        },
                    },
                    "required": ["project", "wiki_identifier", "title"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="list_all_wikis_in_organization",
                description="List all wikis across all projects in the organization for cross-project discovery.",
                inputSchema={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="get_recent_wiki_pages",
                description="Get recently modified wiki pages based on activity.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                        "wiki_identifier": {
                            "type": "string", 
                            "description": "The name or ID of the wiki."
                        },
                        "limit": {
                            "type": "integer", 
                            "description": "Maximum number of pages to return (default: 10)."
                        },
                    },
                    "required": ["project", "wiki_identifier"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="get_wiki_page_suggestions",
                description="Get page suggestions based on partial input - useful for autocomplete-like functionality.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                        "wiki_identifier": {
                            "type": "string", 
                            "description": "The name or ID of the wiki."
                        },
                        "partial_input": {
                            "type": "string", 
                            "description": "Partial page path or title to get suggestions for."
                        },
                    },
                    "required": ["project", "wiki_identifier", "partial_input"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="create_wiki_pages_batch",
                description="Create multiple wiki pages at once for bulk operations.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                        "wiki_identifier": {
                            "type": "string", 
                            "description": "The name or ID of the wiki."
                        },
                        "pages_data": {
                            "type": "array",
                            "description": "Array of page objects to create.",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "path": {
                                        "type": "string",
                                        "description": "The path of the wiki page to create."
                                    },
                                    "content": {
                                        "type": "string",
                                        "description": "The content of the wiki page."
                                    }
                                },
                                "required": ["path", "content"]
                            }
                        },
                    },
                    "required": ["project", "wiki_identifier", "pages_data"],
                    "additionalProperties": False
                }
            ),
            types.Tool(
                name="move_wiki_page",
                description="Move a wiki page from one location to another atomically. Perfect for reorganizing wiki structure.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "project": {
                            "type": "string", 
                            "description": "The name or ID of the project."
                        },
                        "wiki_identifier": {
                            "type": "string", 
                            "description": "The name or ID of the wiki."
                        },
                        "from_path": {
                            "type": "string", 
                            "description": "The current path of the wiki page to move."
                        },
                        "to_path": {
                            "type": "string", 
                            "description": "The target path where the wiki page should be moved."
                        },
                    },
                    "required": ["project", "wiki_identifier", "from_path", "to_path"],
                    "additionalProperties": False
                }
            ),
        ]
        
        logger.info(f"Defined {len(self.tools)} tools")
    
    def _setup_handlers(self):
        """Setup MCP protocol handlers."""
        
        @self.server.list_tools()
        async def list_tools() -> List[types.Tool]:
            """Return the list of available tools."""
            logger.info(f"Tools requested - returning {len(self.tools)} tools")
            self.tools_registered = True
            return self.tools

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Dict[str, Any]) -> List[types.ContentBlock]:
            """Handle tool calls with comprehensive error handling."""
            logger.info(f"Tool called: {name} with arguments: {arguments}")
            
            if not self.client:
                error_msg = "Azure DevOps client not initialized. Please check your configuration."
                logger.error(error_msg)
                return [types.TextContent(type="text", text=f"Error: {error_msg}")]
            
            try:
                result = await self._execute_tool(name, arguments)
                if result is None:
                    error_msg = f"Tool '{name}' not found or returned no result."
                    logger.error(error_msg)
                    return [types.TextContent(type="text", text=f"Error: {error_msg}")]
                
                import json
                response_text = json.dumps(result, indent=2, default=str)
                logger.info(f"Tool {name} executed successfully")
                return [types.TextContent(type="text", text=response_text)]
                
            except Exception as e:
                error_msg = f"Error executing tool '{name}': {str(e)}"
                logger.error(error_msg, exc_info=True)
                return [types.TextContent(type="text", text=f"Error: {error_msg}")]

    async def _execute_tool(self, name: str, arguments: Dict[str, Any]) -> Any:
        """Execute a specific tool with the given arguments."""
        
        # Server health and documentation tools
        if name == "server_health_check":
            return await self._health_check()
        elif name == "list_tools":
            return [tool.name for tool in self.tools]
        elif name == "get_tool_documentation":
            return self._get_tool_documentation(arguments.get("tool_name"))
        
        # Work Item Management
        elif name == "create_work_item":
            work_item = self.client.create_work_item(**arguments)
            return {
                "id": work_item.id,
                "url": work_item.url,
                "title": work_item.fields.get('System.Title', 'N/A')
            }
        elif name == "get_work_item":
            return self.client.get_work_item(**arguments)
        elif name == "update_work_item":
            work_item = self.client.update_work_item(**arguments)
            return {
                "id": work_item.id,
                "url": work_item.url,
                "title": work_item.fields.get('System.Title', 'N/A'),
                "state": work_item.fields.get('System.State', 'N/A')
            }
        elif name == "delete_work_item":
            delete_result = self.client.delete_work_item(**arguments)
            return {
                "message": f"Work item {arguments['work_item_id']} has been deleted successfully.",
                "deleted_date": delete_result.deleted_date.isoformat() if delete_result.deleted_date else None,
                "deleted_by": delete_result.deleted_by.display_name if delete_result.deleted_by else None
            }
        elif name == "search_work_items":
            return self.client.search_work_items(**arguments)
        elif name == "get_work_item_comments":
            return self.client.get_work_item_comments(**arguments)
        
        # Work Item Metadata Discovery
        elif name == "get_work_item_types":
            work_item_types = self.client.get_work_item_types(**arguments)
            return [
                {
                    "name": wit.name,
                    "reference_name": wit.reference_name,
                    "description": getattr(wit, 'description', None),
                    "color": getattr(wit, 'color', None),
                    "icon": getattr(wit, 'icon', None)
                }
                for wit in work_item_types
            ]
        elif name == "get_work_item_states":
            return self.client.get_work_item_states(**arguments)
        elif name == "get_work_item_fields":
            return self.client.get_work_item_fields(**arguments)
        elif name == "get_work_item_transitions":
            return self.client.get_work_item_transitions(**arguments)
        
        # Wiki Management
        elif name == "create_wiki_page":
            page = self.client.create_wiki_page(**arguments)
            return {
                "path": page.page.path,
                "url": page.page.url,
                "content": page.page.content,
            }
        elif name == "get_wiki_page":
            page = self.client.get_wiki_page(**arguments)
            return {
                "path": page.page.path,
                "url": page.page.url,
                "content": page.page.content,
            }
        elif name == "update_wiki_page":
            page = self.client.update_wiki_page(**arguments)
            return {
                "path": page.page.path,
                "url": page.page.url,
                "content": page.page.content,
            }
        elif name == "delete_wiki_page":
            self.client.delete_wiki_page(**arguments)
            return {
                "message": f"Wiki page '{arguments['path']}' deleted successfully.",
                "path": arguments['path']
            }
        elif name == "list_wiki_pages":
            return self.client.list_wiki_pages(**arguments)
        elif name == "get_wikis":
            wikis = self.client.get_wikis(**arguments)
            return [
                {
                    "id": wiki.id,
                    "name": wiki.name,
                    "url": wiki.url,
                    "remote_url": wiki.remote_url,
                }
                for wiki in wikis
            ]
        elif name == "create_wiki":
            wiki = self.client.create_wiki(**arguments)
            return {
                "id": wiki.id,
                "name": wiki.name,
                "url": wiki.url,
                "remote_url": wiki.remote_url,
            }
        
        # Enhanced Wiki Helper Methods
        elif name == "update_wiki_page_safe":
            page = self.client.update_wiki_page_safe(**arguments)
            return {
                "path": page.page.path,
                "url": page.page.url,
                "content": page.page.content,
                "message": "Wiki page updated successfully with safe retry mechanism."
            }
        elif name == "create_or_update_wiki_page_smart":
            page = self.client.create_or_update_wiki_page_smart(**arguments)
            return {
                "path": page.page.path,
                "url": page.page.url,
                "content": page.page.content,
                "message": "Wiki page created or updated successfully."
            }
        elif name == "search_wiki_pages":
            return self.client.search_wiki_pages(**arguments)
        
        # Additional Wiki Navigation Helper Methods
        elif name == "get_wiki_page_tree":
            return self.client.get_wiki_page_tree(**arguments)
        elif name == "find_wiki_by_name":
            return self.client.find_wiki_by_name(**arguments)
        elif name == "get_wiki_page_by_title":
            page = self.client.get_wiki_page_by_title(**arguments)
            if page:
                return {
                    "path": page.page.path,
                    "url": page.page.url,
                    "content": page.page.content,
                }
            else:
                return {"message": f"No page found with title '{arguments['title']}'"}
        elif name == "list_all_wikis_in_organization":
            return self.client.list_all_wikis_in_organization()
        elif name == "get_recent_wiki_pages":
            return self.client.get_recent_wiki_pages(**arguments)
        elif name == "get_wiki_page_suggestions":
            return self.client.get_wiki_page_suggestions(**arguments)
        elif name == "create_wiki_pages_batch":
            return self.client.create_wiki_pages_batch(**arguments)
        elif name == "move_wiki_page":
            return self.client.move_wiki_page(**arguments)
        
        # Repository Management
        elif name == "list_repositories":
            return self.client.list_repositories(**arguments)
        elif name == "list_files":
            return self.client.list_files(**arguments)
        elif name == "get_file_content":
            return self.client.get_file_content(**arguments)
        
        # Project Management
        elif name == "set_project_context":
            return self.client.set_project_context(**arguments)
        elif name == "clear_project_context":
            return self.client.clear_project_context()
        elif name == "get_projects":
            projects = self.client.get_projects()
            return {"projects": [p.name for p in projects]}
        
        else:
            logger.warning(f"Unknown tool: {name}")
            return None

    async def _health_check(self) -> Dict[str, Any]:
        """Perform comprehensive health check."""
        health_status = {
            "server_status": "healthy",
            "environment_check": self._validate_environment(),
            "client_initialized": self.client is not None,
            "tools_registered": self.tools_registered,
            "total_tools": len(self.tools),
            "azure_devops_connection": "unknown"
        }
        
        if self.client:
            try:
                # Test Azure DevOps connection
                projects = self.client.get_projects()
                health_status["azure_devops_connection"] = "connected"
                health_status["available_projects"] = len(projects)
            except Exception as e:
                health_status["azure_devops_connection"] = f"error: {str(e)}"
        
        return health_status

    def _get_tool_documentation(self, tool_name: str) -> Dict[str, Any]:
        """Get documentation for a specific tool."""
        tool = next((t for t in self.tools if t.name == tool_name), None)
        if tool:
            return {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema,
            }
        else:
            return {"error": f"Tool '{tool_name}' not found."}

    async def run(self):
        """Run the MCP server with proper initialization and error handling."""
        logger.info("Starting MCP Azure DevOps Server...")
        
        # Validate environment
        if not self._validate_environment():
            logger.error("Environment validation failed. Server cannot start.")
            sys.exit(1)
        
        # Initialize client
        if not self._initialize_client():
            logger.error("Client initialization failed. Server cannot start.")
            sys.exit(1)
        
        logger.info("Server initialization completed successfully")
        logger.info(f"Registered {len(self.tools)} tools")
        
        try:
            async with stdio_server() as (read_stream, write_stream):
                logger.info("Starting MCP protocol communication...")
                await self.server.run(
                    read_stream,
                    write_stream,
                    self.server.create_initialization_options(),
                )
        except Exception as e:
            logger.error(f"Server runtime error: {e}", exc_info=True)
            raise

def main():
    """Main entry point for the MCP server."""
    try:
        server = MCPAzureDevOpsServer()
        asyncio.run(server.run())
    except KeyboardInterrupt:
        logger.info("Server shutdown requested by user")
    except Exception as e:
        logger.error(f"Fatal server error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
