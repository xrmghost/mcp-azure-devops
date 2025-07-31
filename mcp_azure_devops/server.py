import os
from mcp.server import Mcp
from mcp.tool import McpTool, McpToolSchema
from .azure_devops_client import AzureDevOpsClient

def main():
    """
    Main function to run the MCP server.
    """
    mcp = Mcp()
    client = AzureDevOpsClient()

    create_work_item_tool = McpTool(
        "create_work_item",
        "Creates a new work item in Azure DevOps.",
        lambda project, work_item_type, title, description: client.create_work_item(project, work_item_type, title, description),
        McpToolSchema(
            properties={
                "project": {"type": "string", "description": "The name or ID of the project."},
                "work_item_type": {"type": "string", "description": "The type of work item (e.g., 'Bug', 'User Story')."},
                "title": {"type": "string", "description": "The title of the work item."},
                "description": {"type": "string", "description": "The description of the work item."},
            },
            required=["project", "work_item_type", "title", "description"],
        )
    )
    mcp.add_tool(create_work_item_tool)

    get_work_item_tool = McpTool(
        "get_work_item",
        "Gets a work item by its ID.",
        lambda work_item_id: client.get_work_item(work_item_id),
        McpToolSchema(
            properties={
                "work_item_id": {"type": "integer", "description": "The ID of the work item."},
            },
            required=["work_item_id"],
        )
    )
    mcp.add_tool(get_work_item_tool)

    update_work_item_tool = McpTool(
        "update_work_item",
        "Updates a work item by its ID.",
        lambda work_item_id, updates: client.update_work_item(work_item_id, updates),
        McpToolSchema(
            properties={
                "work_item_id": {"type": "integer", "description": "The ID of the work item to update."},
                "updates": {"type": "object", "description": "A dictionary of fields to update."},
            },
            required=["work_item_id", "updates"],
        )
    )
    mcp.add_tool(update_work_item_tool)

    delete_work_item_tool = McpTool(
        "delete_work_item",
        "Deletes a work item by its ID.",
        lambda work_item_id: client.delete_work_item(work_item_id),
        McpToolSchema(
            properties={
                "work_item_id": {"type": "integer", "description": "The ID of the work item to delete."},
            },
            required=["work_item_id"],
        )
    )
    mcp.add_tool(delete_work_item_tool)

    search_work_items_tool = McpTool(
        "search_work_items",
        "Searches for work items using a WIQL query.",
        lambda project, wiql_query: client.search_work_items(project, wiql_query),
        McpToolSchema(
            properties={
                "project": {"type": "string", "description": "The name or ID of the project."},
                "wiql_query": {"type": "string", "description": "The Work Item Query Language (WIQL) query."},
            },
            required=["project", "wiql_query"],
        )
    )
    mcp.add_tool(search_work_items_tool)

    create_wiki_page_tool = McpTool(
        "create_wiki_page",
        "Creates or updates a wiki page.",
        lambda project, wiki_identifier, path, content: client.create_wiki_page(project, wiki_identifier, path, content),
        McpToolSchema(
            properties={
                "project": {"type": "string", "description": "The name or ID of the project."},
                "wiki_identifier": {"type": "string", "description": "The name or ID of the wiki."},
                "path": {"type": "string", "description": "The path of the wiki page."},
                "content": {"type": "string", "description": "The content of the wiki page."},
            },
            required=["project", "wiki_identifier", "path", "content"],
        )
    )
    mcp.add_tool(create_wiki_page_tool)

    get_wiki_page_tool = McpTool(
        "get_wiki_page",
        "Gets a wiki page by its path.",
        lambda project, wiki_identifier, path: client.get_wiki_page(project, wiki_identifier, path),
        McpToolSchema(
            properties={
                "project": {"type": "string", "description": "The name or ID of the project."},
                "wiki_identifier": {"type": "string", "description": "The name or ID of the wiki."},
                "path": {"type": "string", "description": "The path of the wiki page."},
            },
            required=["project", "wiki_identifier", "path"],
        )
    )
    mcp.add_tool(get_wiki_page_tool)

    delete_wiki_page_tool = McpTool(
        "delete_wiki_page",
        "Deletes a wiki page by its path.",
        lambda project, wiki_identifier, path: client.delete_wiki_page(project, wiki_identifier, path),
        McpToolSchema(
            properties={
                "project": {"type": "string", "description": "The name or ID of the project."},
                "wiki_identifier": {"type": "string", "description": "The name or ID of the wiki."},
                "path": {"type": "string", "description": "The path of the wiki page to delete."},
            },
            required=["project", "wiki_identifier", "path"],
        )
    )
    mcp.add_tool(delete_wiki_page_tool)

    list_wiki_pages_tool = McpTool(
        "list_wiki_pages",
        "Lists all pages in a wiki.",
        lambda project, wiki_identifier: client.list_wiki_pages(project, wiki_identifier),
        McpToolSchema(
            properties={
                "project": {"type": "string", "description": "The name or ID of the project."},
                "wiki_identifier": {"type": "string", "description": "The name or ID of the wiki."},
            },
            required=["project", "wiki_identifier"],
        )
    )
    mcp.add_tool(list_wiki_pages_tool)

    list_repositories_tool = McpTool(
        "list_repositories",
        "Lists all repositories in a project.",
        lambda project: client.list_repositories(project),
        McpToolSchema(
            properties={
                "project": {"type": "string", "description": "The name or ID of the project."},
            },
            required=["project"],
        )
    )
    mcp.add_tool(list_repositories_tool)

    list_files_tool = McpTool(
        "list_files",
        "Lists files in a repository.",
        lambda project, repository_id, path: client.list_files(project, repository_id, path),
        McpToolSchema(
            properties={
                "project": {"type": "string", "description": "The name or ID of the project."},
                "repository_id": {"type": "string", "description": "The name or ID of the repository."},
                "path": {"type": "string", "description": "The path to list files from."},
            },
            required=["project", "repository_id", "path"],
        )
    )
    mcp.add_tool(list_files_tool)

    get_file_content_tool = McpTool(
        "get_file_content",
        "Gets the content of a file in a repository.",
        lambda project, repository_id, path: client.get_file_content(project, repository_id, path),
        McpToolSchema(
            properties={
                "project": {"type": "string", "description": "The name or ID of the project."},
                "repository_id": {"type": "string", "description": "The name or ID of the repository."},
                "path": {"type": "string", "description": "The path to the file."},
            },
            required=["project", "repository_id", "path"],
        )
    )
    mcp.add_tool(get_file_content_tool)

    set_project_context_tool = McpTool(
        "set_project_context",
        "Sets the project context for subsequent commands.",
        lambda project: client.set_project_context(project),
        McpToolSchema(
            properties={
                "project": {"type": "string", "description": "The name or ID of the project to set as context."},
            },
            required=["project"],
        )
    )
    mcp.add_tool(set_project_context_tool)

    clear_project_context_tool = McpTool(
        "clear_project_context",
        "Clears the project context.",
        lambda: client.clear_project_context(),
        McpToolSchema()
    )
    mcp.add_tool(clear_project_context_tool)

    mcp.run()

if __name__ == "__main__":
    main()
