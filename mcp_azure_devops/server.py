import os
from mcp.server import Server
from mcp.types import Tool
from .azure_devops_client import AzureDevOpsClient

def main():
    """
    Main function to run the MCP server.
    """
    mcp = Server()
    client = AzureDevOpsClient()

    create_work_item_tool = Tool(
        name="create_work_item",
        description="Creates a new work item in Azure DevOps.",
        handler=lambda project, work_item_type, title, description: client.create_work_item(project, work_item_type, title, description),
        inputSchema={
            "properties": {
                "project": {"type": "string", "description": "The name or ID of the project."},
                "work_item_type": {"type": "string", "description": "The type of work item (e.g., 'Bug', 'User Story')."},
                "title": {"type": "string", "description": "The title of the work item."},
                "description": {"type": "string", "description": "The description of the work item."},
            },
            "required": ["project", "work_item_type", "title", "description"],
        }
    )
    mcp.add_tool(create_work_item_tool)

    get_work_item_tool = Tool(
        name="get_work_item",
        description="Gets a work item by its ID.",
        handler=lambda work_item_id: client.get_work_item(work_item_id),
        inputSchema={
            "properties": {
                "work_item_id": {"type": "integer", "description": "The ID of the work item."},
            },
            "required": ["work_item_id"],
        }
    )
    mcp.add_tool(get_work_item_tool)

    update_work_item_tool = Tool(
        name="update_work_item",
        description="Updates a work item by its ID.",
        handler=lambda work_item_id, updates: client.update_work_item(work_item_id, updates),
        inputSchema={
            "properties": {
                "work_item_id": {"type": "integer", "description": "The ID of the work item to update."},
                "updates": {"type": "object", "description": "A dictionary of fields to update."},
            },
            "required": ["work_item_id", "updates"],
        }
    )
    mcp.add_tool(update_work_item_tool)

    delete_work_item_tool = Tool(
        name="delete_work_item",
        description="Deletes a work item by its ID.",
        handler=lambda work_item_id: client.delete_work_item(work_item_id),
        inputSchema={
            "properties": {
                "work_item_id": {"type": "integer", "description": "The ID of the work item to delete."},
            },
            "required": ["work_item_id"],
        }
    )
    mcp.add_tool(delete_work_item_tool)

    search_work_items_tool = Tool(
        name="search_work_items",
        description="Searches for work items using a WIQL query.",
        handler=lambda project, wiql_query: client.search_work_items(project, wiql_query),
        inputSchema={
            "properties": {
                "project": {"type": "string", "description": "The name or ID of the project."},
                "wiql_query": {"type": "string", "description": "The Work Item Query Language (WIQL) query."},
            },
            "required": ["project", "wiql_query"],
        }
    )
    mcp.add_tool(search_work_items_tool)

    create_wiki_page_tool = Tool(
        name="create_wiki_page",
        description="Creates or updates a wiki page.",
        handler=lambda project, wiki_identifier, path, content: client.create_wiki_page(project, wiki_identifier, path, content),
        inputSchema={
            "properties": {
                "project": {"type": "string", "description": "The name or ID of the project."},
                "wiki_identifier": {"type": "string", "description": "The name or ID of the wiki."},
                "path": {"type": "string", "description": "The path of the wiki page."},
                "content": {"type": "string", "description": "The content of the wiki page."},
            },
            "required": ["project", "wiki_identifier", "path", "content"],
        }
    )
    mcp.add_tool(create_wiki_page_tool)

    get_wiki_page_tool = Tool(
        name="get_wiki_page",
        description="Gets a wiki page by its path.",
        handler=lambda project, wiki_identifier, path: client.get_wiki_page(project, wiki_identifier, path),
        inputSchema={
            "properties": {
                "project": {"type": "string", "description": "The name or ID of the project."},
                "wiki_identifier": {"type": "string", "description": "The name or ID of the wiki."},
                "path": {"type": "string", "description": "The path of the wiki page."},
            },
            "required": ["project", "wiki_identifier", "path"],
        }
    )
    mcp.add_tool(get_wiki_page_tool)

    delete_wiki_page_tool = Tool(
        name="delete_wiki_page",
        description="Deletes a wiki page by its path.",
        handler=lambda project, wiki_identifier, path: client.delete_wiki_page(project, wiki_identifier, path),
        inputSchema={
            "properties": {
                "project": {"type": "string", "description": "The name or ID of the project."},
                "wiki_identifier": {"type": "string", "description": "The name or ID of the wiki."},
                "path": {"type": "string", "description": "The path of the wiki page to delete."},
            },
            "required": ["project", "wiki_identifier", "path"],
        }
    )
    mcp.add_tool(delete_wiki_page_tool)

    list_wiki_pages_tool = Tool(
        name="list_wiki_pages",
        description="Lists all pages in a wiki.",
        handler=lambda project, wiki_identifier: client.list_wiki_pages(project, wiki_identifier),
        inputSchema={
            "properties": {
                "project": {"type": "string", "description": "The name or ID of the project."},
                "wiki_identifier": {"type": "string", "description": "The name or ID of the wiki."},
            },
            "required": ["project", "wiki_identifier"],
        }
    )
    mcp.add_tool(list_wiki_pages_tool)

    list_repositories_tool = Tool(
        name="list_repositories",
        description="Lists all repositories in a project.",
        handler=lambda project: client.list_repositories(project),
        inputSchema={
            "properties": {
                "project": {"type": "string", "description": "The name or ID of the project."},
            },
            "required": ["project"],
        }
    )
    mcp.add_tool(list_repositories_tool)

    list_files_tool = Tool(
        name="list_files",
        description="Lists files in a repository.",
        handler=lambda project, repository_id, path: client.list_files(project, repository_id, path),
        inputSchema={
            "properties": {
                "project": {"type": "string", "description": "The name or ID of the project."},
                "repository_id": {"type": "string", "description": "The name or ID of the repository."},
                "path": {"type": "string", "description": "The path to list files from."},
            },
            "required": ["project", "repository_id", "path"],
        }
    )
    mcp.add_tool(list_files_tool)

    get_file_content_tool = Tool(
        name="get_file_content",
        description="Gets the content of a file in a repository.",
        handler=lambda project, repository_id, path: client.get_file_content(project, repository_id, path),
        inputSchema={
            "properties": {
                "project": {"type": "string", "description": "The name or ID of the project."},
                "repository_id": {"type": "string", "description": "The name or ID of the repository."},
                "path": {"type": "string", "description": "The path to the file."},
            },
            "required": ["project", "repository_id", "path"],
        }
    )
    mcp.add_tool(get_file_content_tool)

    set_project_context_tool = Tool(
        name="set_project_context",
        description="Sets the project context for subsequent commands.",
        handler=lambda project: client.set_project_context(project),
        inputSchema={
            "properties": {
                "project": {"type": "string", "description": "The name or ID of the project to set as context."},
            },
            "required": ["project"],
        }
    )
    mcp.add_tool(set_project_context_tool)

    clear_project_context_tool = Tool(
        name="clear_project_context",
        description="Clears the project context.",
        handler=lambda: client.clear_project_context(),
        inputSchema={}
    )
    mcp.add_tool(clear_project_context_tool)

    mcp.run()

if __name__ == "__main__":
    main()
