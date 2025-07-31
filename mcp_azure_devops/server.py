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
            result = client.update_work_item(**arguments)
        elif name == "delete_work_item":
            result = client.delete_work_item(**arguments)
        elif name == "search_work_items":
            result = client.search_work_items(**arguments)
        elif name == "create_wiki_page":
            result = client.create_wiki_page(**arguments)
        elif name == "get_wiki_page":
            result = client.get_wiki_page(**arguments)
        elif name == "delete_wiki_page":
            result = client.delete_wiki_page(**arguments)
        elif name == "list_wiki_pages":
            result = client.list_wiki_pages(**arguments)
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
