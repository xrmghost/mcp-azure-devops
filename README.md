# mcp-azure-devops

An open-source Model Context Protocol (MCP) server for seamless integration with Azure DevOps.

## Mission

To create a robust, open-source Model Context Protocol (MCP) server that provides seamless integration with Azure DevOps. This server will empower AI agents to interact with Azure DevOps projects, managing work items, wikis, and repositories, thereby streamlining development workflows.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Core Features

The MCP server will expose a set of tools to interact with Azure DevOps, categorized by area.

### Implemented Features

#### Work Item Management (CRUD)
-   `create_work_item` (supports Epic, User Story, Task, Bug, and work item linking)
-   `get_work_item` (by ID)
-   `update_work_item` (by ID, supports work item linking)
-   `delete_work_item` (by ID)
-   `search_work_items` (using WIQL - Work Item Query Language)
-   `get_work_item_comments` (retrieve comments for a work item with pagination support)

#### Wiki Management (CRUD)
-   `create_wiki_page`
-   `get_wiki_page` (by path)
-   `update_wiki_page` (by path)
-   `delete_wiki_page` (by path)
-   `list_wiki_pages`
-   `get_wikis`
-   `create_wiki`

#### Enhanced Wiki Helper Methods
-   `update_wiki_page_safe`: Safely updates a wiki page with automatic retry on version conflicts
-   `create_or_update_wiki_page_smart`: Creates a new wiki page or updates existing one intelligently
-   `search_wiki_pages`: Search for wiki pages by title or content
-   `get_wiki_page_tree`: Get hierarchical structure of wiki pages
-   `find_wiki_by_name`: Find wikis by partial name match
-   `get_wiki_page_by_title`: Find wiki page by title instead of exact path
-   `list_all_wikis_in_organization`: List all wikis across all projects in the organization
-   `get_recent_wiki_pages`: Get recently modified wiki pages
-   `get_wiki_page_suggestions`: Get page suggestions based on partial input
-   `create_wiki_pages_batch`: Create multiple wiki pages at once

#### Repository Management (Read-only)
-   `list_repositories`
-   `list_files` (in a repository)
-   `get_file_content`

#### Project Scoping
-   `set_project_context`: A special tool to set the active project for subsequent commands.
-   `clear_project_context`: To revert to the organization-level scope.
-   `get_projects`: To list all projects in the organization.

#### Server Documentation
-   `list_available_tools`: Lists all available tools.
-   `get_tool_documentation`: Gets the documentation for a specific tool.

#### User Management (Under Development)
-   `list_users`: Lists all users in the organization.
    -   **Note:** This feature is currently under development and requires a Personal Access Token (PAT) with **Graph (Read)** permissions.

### Planned Features

-   **Repository Management (Write operations):**
    -   `create_repository`
    -   `create_pull_request`
    -   `manage_branches`
-   **Pipeline Management:**
    -   `trigger_build`
    -   `get_build_status`
    -   `list_pipelines`

## Getting Started

This guide will walk you through setting up the `mcp-azure-devops` server.

### Prerequisites
- Python 3.10 or higher
- `pip` and `venv` for managing Python packages

### Installation Steps

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/xrmghost/mcp-azure-devops.git
    cd mcp-azure-devops
    ```

2.  **Create and Activate a Virtual Environment:**
    It's highly recommended to use a virtual environment to manage the project's dependencies.
    ```bash
    # For Windows
    python -m venv .venv
    .\.venv\Scripts\activate

    # For macOS/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Dependencies:**
    Install the project and its dependencies in editable mode.
    ```bash
    pip install -e .
    ```

4.  **Validate Your Setup:**
    Run the validation script to ensure everything is configured correctly:
    ```bash
    python validate_setup.py
    ```
    This script will check your Python version, dependencies, environment variables, and Azure DevOps connectivity.

### Configuration

1.  **Generate an Azure DevOps Personal Access Token (PAT):**
    -   Navigate to your Azure DevOps organization.
    -   Go to **User settings** > **Personal Access Tokens**.
    -   Click **+ New Token**.
    -   Give your token a name (e.g., `mcp-server-token`).
    -   Select the organization.
    -   Set the expiration date.
    -   For the scopes, you will need to grant the following permissions at a minimum:
        -   **Work Items:** Read & write
        -   **Wiki:** Read & write
        -   **Code:** Read
        -   **Graph:** Read (for the `list_users` feature)
    -   Click **Create** and **copy the token immediately**. You will not be able to see it again.

2.  **Configure the MCP Server in Cline:**
    -   Open your `cline_mcp_settings.json` file.
    -   > **Note:** The location of this file can vary. A common location on Windows is `C:\Users\<YourUsername>\AppData\Roaming\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json`. If you can't find it, you can search your user's home directory for the file.
    -   Add a new entry for the `mcp-azure-devops` server. The command should be `mcp-azure-devops`.

    Here is an example configuration. You must use the **full, absolute path** to the `mcp-azure-devops.exe` executable created inside your virtual environment.
    ```json
    {
      "mcpServers": {
        "mcp-azure-devops": {
          "command": "C:\\path\\to\\your\\project\\mcp-azure-devops\\.venv\\Scripts\\mcp-azure-devops.exe",
          "args": [],
          "env": {
            "AZURE_DEVOPS_ORG_URL": "https://dev.azure.com/your-organization",
            "AZURE_DEVOPS_PAT": "your-personal-access-token"
          },
          "disabled": false,
          "autoApprove": []
        }
      }
    }
    ```
    -   Replace `your-organization` with your Azure DevOps organization name and `your-personal-access-token` with the PAT you generated.

3.  **Restart Cline:**
    Restart your Cline application to load the new MCP server.

## Troubleshooting

If you encounter issues with the MCP server, follow these steps:

### Quick Diagnosis
1. **Run the validation script:**
   ```bash
   python validate_setup.py
   ```
   This will identify common configuration and setup issues.

2. **Check server logs:**
   ```bash
   python -m mcp_azure_devops.server 2> server.log
   ```
   Look for error messages in the log output.

### Common Issues

#### "No tools found" in VS Code
- **Cause:** MCP protocol communication issues or incorrect configuration
- **Solution:** Verify your `cline_mcp_settings.json` configuration and restart VS Code

#### Server fails to start
- **Cause:** Missing dependencies or environment variables
- **Solution:** Run `python validate_setup.py` to identify specific issues

#### Azure DevOps connection failures
- **Cause:** Invalid PAT or network issues
- **Solution:** Verify your Personal Access Token and organization URL

For detailed troubleshooting guidance, see the [Troubleshooting Guide](TROUBLESHOOTING.md).

### Built-in Diagnostics

The server includes a health check tool that you can use to verify everything is working:

```json
{
  "tool": "server_health_check",
  "arguments": {}
}
```

This will return comprehensive status information about your server configuration and Azure DevOps connectivity.

## Wiki Helper Methods

The server includes enhanced wiki helper methods that solve common issues with wiki management:

- **Update Failures**: Safe update methods with automatic retry on version conflicts
- **Navigation Difficulties**: Search and discovery methods to find wikis and pages easily
- **Limited Helper Methods**: Comprehensive set of helper methods for better user experience

For detailed usage instructions and examples, see the [Wiki Helper Methods Guide](WIKI_HELPER_GUIDE.md).

## Acknowledgements

This project was inspired by the `mcp-atlassian` server, which provides similar functionality for Jira and Confluence. You can find it here: [https://github.com/pashpashpash/mcp-atlassian](https://github.com/pashpashpash/mcp-atlassian).
