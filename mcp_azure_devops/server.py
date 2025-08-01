import os
import asyncio
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.server.stdio import stdio_server
from .azure_devops_client import AzureDevOpsClient

def main():
    """
    Main function to run the MCP server.
    """
    server = Server(name="mcp-azure-devops", version="0.1.0")
    client = AzureDevOpsClient()

    tools = [
        types.Tool(
            name="create_work_item",
            description="Creates a new work item in Azure DevOps.",
            inputSchema={
                "properties": {
                    "project": {"type": "string", "description": "The name or ID of the project."},
                    "work_item_type": {"type": "string", "description": "The type of work item (e.g., 'Bug', 'User Story')."},
                    "title": {"type": "string", "description": "The title of the work item."},
                    "description": {"type": "string", "description": "The description of the work item."},
                    "relations": {
                        "type": "array",
                        "description": "A list of relations to other work items.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "rel": {"type": "string", "description": "The relation type (e.g., 'System.LinkTypes.Dependency-Forward')."},
                                "url": {"type": "string", "description": "The URL of the related work item."}
                            },
                            "required": ["rel", "url"]
                        }
                    }
                },
                "required": ["project", "work_item_type", "title", "description"],
            }
        ),
        types.Tool(
            name="get_work_item",
            description="Gets a work item by its ID.",
            inputSchema={
                "properties": {
                    "work_item_id": {"type": "integer", "description": "The ID of the work item."},
                    "expand": {"type": "string", "description": "The expand option for the work item. Use 'All' to get all fields."},
                },
                "required": ["work_item_id"],
            }
        ),
        types.Tool(
            name="update_work_item",
            description="Updates a work item by its ID.",
            inputSchema={
                "properties": {
                    "work_item_id": {"type": "integer", "description": "The ID of the work item to update."},
                    "updates": {"type": "object", "description": "A dictionary of fields to update."},
                    "relations": {
                        "type": "array",
                        "description": "A list of relations to other work items.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "rel": {"type": "string", "description": "The relation type (e.g., 'System.LinkTypes.Dependency-Forward')."},
                                "url": {"type": "string", "description": "The URL of the related work item."}
                            },
                            "required": ["rel", "url"]
                        }
                    }
                },
                "required": ["work_item_id", "updates"],
            }
        ),
        types.Tool(
            name="delete_work_item",
            description="Deletes a work item by its ID.",
            inputSchema={
                "properties": {
                    "work_item_id": {"type": "integer", "description": "The ID of the work item to delete."},
                },
                "required": ["work_item_id"],
            }
        ),
        types.Tool(
            name="search_work_items",
            description="Searches for work items using a WIQL query.",
            inputSchema={
                "properties": {
                    "project": {"type": "string", "description": "The name or ID of the project."},
                    "wiql_query": {"type": "string", "description": "The Work Item Query Language (WIQL) query."},
                },
                "required": ["project", "wiql_query"],
            }
        ),
        types.Tool(
            name="create_wiki_page",
            description="Creates or updates a wiki page.",
            inputSchema={
                "properties": {
                    "project": {"type": "string", "description": "The name or ID of the project."},
                    "wiki_identifier": {"type": "string", "description": "The name or ID of the wiki."},
                    "path": {"type": "string", "description": "The path of the wiki page."},
                    "content": {"type": "string", "description": "The content of the wiki page."},
                },
                "required": ["project", "wiki_identifier", "path", "content"],
            }
        ),
        types.Tool(
            name="get_wiki_page",
            description="Gets a wiki page by its path.",
            inputSchema={
                "properties": {
                    "project": {"type": "string", "description": "The name or ID of the project."},
                    "wiki_identifier": {"type": "string", "description": "The name or ID of the wiki."},
                    "path": {"type": "string", "description": "The path of the wiki page."},
                },
                "required": ["project", "wiki_identifier", "path"],
            }
        ),
        types.Tool(
            name="update_wiki_page",
            description="Updates a wiki page.",
            inputSchema={
                "properties": {
                    "project": {"type": "string", "description": "The name or ID of the project."},
                    "wiki_identifier": {"type": "string", "description": "The name or ID of the wiki."},
                    "path": {"type": "string", "description": "The path of the wiki page."},
                    "content": {"type": "string", "description": "The content of the wiki page."},
                },
                "required": ["project", "wiki_identifier", "path", "content"],
            }
        ),
        types.Tool(
            name="delete_wiki_page",
            description="Deletes a wiki page by its path.",
            inputSchema={
                "properties": {
                    "project": {"type": "string", "description": "The name or ID of the project."},
                    "wiki_identifier": {"type": "string", "description": "The name or ID of the wiki."},
                    "path": {"type": "string", "description": "The path of the wiki page to delete."},
                },
                "required": ["project", "wiki_identifier", "path"],
            }
        ),
        types.Tool(
            name="list_wiki_pages",
            description="Lists all pages in a wiki.",
            inputSchema={
                "properties": {
                    "project": {"type": "string", "description": "The name or ID of the project."},
                    "wiki_identifier": {"type": "string", "description": "The name or ID of the wiki."},
                },
                "required": ["project", "wiki_identifier"],
            }
        ),
        types.Tool(
            name="get_wikis",
            description="Gets all wikis in a project.",
            inputSchema={
                "properties": {
                    "project": {"type": "string", "description": "The name or ID of the project."},
                },
                "required": ["project"],
            }
        ),
        types.Tool(
            name="create_wiki",
            description="Creates a new wiki in a project.",
            inputSchema={
                "properties": {
                    "project": {"type": "string", "description": "The name or ID of the project."},
                    "name": {"type": "string", "description": "The name of the wiki to create."},
                },
                "required": ["project", "name"],
            }
        ),
        types.Tool(
            name="list_repositories",
            description="Lists all repositories in a project.",
            inputSchema={
                "properties": {
                    "project": {"type": "string", "description": "The name or ID of the project."},
                },
                "required": ["project"],
            }
        ),
        types.Tool(
            name="list_files",
            description="Lists files in a repository.",
            inputSchema={
                "properties": {
                    "project": {"type": "string", "description": "The name or ID of the project."},
                    "repository_id": {"type": "string", "description": "The name or ID of the repository."},
                    "path": {"type": "string", "description": "The path to list files from."},
                },
                "required": ["project", "repository_id", "path"],
            }
        ),
        types.Tool(
            name="get_file_content",
            description="Gets the content of a file in a repository.",
            inputSchema={
                "properties": {
                    "project": {"type": "string", "description": "The name or ID of the project."},
                    "repository_id": {"type": "string", "description": "The name or ID of the repository."},
                    "path": {"type": "string", "description": "The path to the file."},
                },
                "required": ["project", "repository_id", "path"],
            }
        ),
        types.Tool(
            name="set_project_context",
            description="Sets the project context for subsequent commands.",
            inputSchema={
                "properties": {
                    "project": {"type": "string", "description": "The name or ID of the project to set as context."},
                },
                "required": ["project"],
            }
        ),
        types.Tool(
            name="clear_project_context",
            description="Clears the project context.",
            inputSchema={}
        ),
        types.Tool(
            name="get_projects",
            description="Gets a list of all projects in the organization.",
            inputSchema={}
        ),
        types.Tool(
            name="list_tools",
            description="Lists all available tools.",
            inputSchema={}
        ),
        types.Tool(
            name="list_available_tools",
            description="Lists all available tools. Alias for list_tools.",
            inputSchema={}
        ),
        types.Tool(
            name="get_tool_documentation",
            description="Gets the documentation for a specific tool.",
            inputSchema={
                "properties": {
                    "tool_name": {"type": "string", "description": "The name of the tool to get documentation for."},
                },
                "required": ["tool_name"],
            }
        ),
        types.Tool(
            name="docs",
            description="Gets the documentation for a specific tool.",
            inputSchema={
                "properties": {
                    "tool_name": {"type": "string", "description": "The name of the tool to get documentation for."},
                },
                "required": ["tool_name"],
            }
        ),
        types.Tool(
            name="help",
            description="Gets the documentation for a specific tool.",
            inputSchema={
                "properties": {
                    "tool_name": {"type": "string", "description": "The name of the tool to get documentation for."},
                },
                "required": ["tool_name"],
            }
        ),
        types.Tool(
            name="get_documentation",
            description="Gets the documentation for a specific tool.",
            inputSchema={
                "properties": {
                    "tool_name": {"type": "string", "description": "The name of the tool to get documentation for."},
                },
                "required": ["tool_name"],
            }
        ),
    ]

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return tools

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[types.ContentBlock]:
        result = None
        if name == "create_work_item":
            work_item = client.create_work_item(**arguments)
            result = {
                "id": work_item.id,
                "url": work_item.url,
                "title": work_item.fields['System.Title']
            }
        elif name == "get_work_item":
            result = client.get_work_item(**arguments)
        elif name == "update_work_item":
            work_item = client.update_work_item(**arguments)
            result = {
                "id": work_item.id,
                "url": work_item.url,
                "title": work_item.fields['System.Title'],
                "state": work_item.fields['System.State']
            }
        elif name == "delete_work_item":
            delete_result = client.delete_work_item(**arguments)
            result = {
                "message": f"Work item {arguments['work_item_id']} has been deleted successfully.",
                "deleted_date": delete_result.deleted_date.isoformat() if delete_result.deleted_date else None,
                "deleted_by": delete_result.deleted_by.display_name if delete_result.deleted_by else None
            }
        elif name == "search_work_items":
            result = client.search_work_items(**arguments)
        elif name == "create_wiki_page":
            page = client.create_wiki_page(**arguments)
            result = {
                "path": page.page.path,
                "url": page.page.url,
                "content": page.page.content,
            }
        elif name == "get_wiki_page":
            page = client.get_wiki_page(**arguments)
            result = {
                "path": page.page.path,
                "url": page.page.url,
                "content": page.page.content,
            }
        elif name == "update_wiki_page":
            page = client.update_wiki_page(**arguments)
            result = {
                "path": page.page.path,
                "url": page.page.url,
                "content": page.page.content,
            }
        elif name == "delete_wiki_page":
            deleted_page = client.delete_wiki_page(**arguments)
            result = {
                "message": f"Wiki page '{arguments['path']}' deleted successfully.",
                "path": deleted_page.path,
                "url": deleted_page.url,
            }
        elif name == "list_wiki_pages":
            result = client.list_wiki_pages(**arguments)
        elif name == "get_wikis":
            wikis = client.get_wikis(**arguments)
            result = [
                {
                    "id": wiki.id,
                    "name": wiki.name,
                    "url": wiki.url,
                    "remote_url": wiki.remote_url,
                }
                for wiki in wikis
            ]
        elif name == "create_wiki":
            wiki = client.create_wiki(**arguments)
            result = {
                "id": wiki.id,
                "name": wiki.name,
                "url": wiki.url,
                "remote_url": wiki.remote_url,
            }
        elif name == "list_repositories":
            result = client.list_repositories(**arguments)
        elif name == "list_files":
            result = client.list_files(**arguments)
        elif name == "get_file_content":
            result = client.get_file_content(**arguments)
        elif name == "set_project_context":
            result = client.set_project_context(**arguments)
        elif name == "clear_project_context":
            result = client.clear_project_context()
        elif name == "get_projects":
            projects = client.get_projects()
            project_names = [p.name for p in projects]
            result = {"projects": project_names}
        elif name in ["list_tools", "list_available_tools"]:
            result = [tool.name for tool in tools]
        elif name in ["get_tool_documentation", "docs", "help", "get_documentation"]:
            tool_name = arguments.get("tool_name")
            tool_doc = next((tool for tool in tools if tool.name == tool_name), None)
            if tool_doc:
                result = {
                    "name": tool_doc.name,
                    "description": tool_doc.description,
                    "inputSchema": tool_doc.inputSchema,
                }
            else:
                result = {"error": f"Tool '{tool_name}' not found."}
        
        if result is None:
            return [types.TextContent(type="text", text=f"Tool '{name}' not found.")]

        import json
        return [types.TextContent(type="text", text=json.dumps(result, indent=2))]

    async def run_server():
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options(),
            )

    asyncio.run(run_server())

if __name__ == "__main__":
    main()
