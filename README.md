# mcp-azure-devops

An open-source Model Context Protocol (MCP) server for seamless integration with Azure DevOps.

## Mission

To create a robust, open-source Model Context Protocol (MCP) server that provides seamless integration with Azure DevOps. This server will empower AI agents to interact with Azure DevOps projects, managing work items, wikis, and repositories, thereby streamlining development workflows.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Core Features

The MCP server will expose a set of tools to interact with Azure DevOps, categorized by area:

### Work Item Management (CRUD)
-   `create_work_item` (supports Epic, User Story, Task, Bug)
-   `get_work_item` (by ID)
-   `update_work_item` (by ID)
-   `delete_work_item` (by ID)
-   `search_work_items` (using WIQL - Work Item Query Language)

### Wiki Management (CRUD)
-   `create_wiki_page`
-   `get_wiki_page` (by path)
-   `update_wiki_page` (by path)
-   `delete_wiki_page` (by path)
-   `list_wiki_pages`

### Repository Management (Read-only)
-   `list_repositories`
-   `list_files` (in a repository)
-   `get_file_content`

### Project Scoping
-   `set_project_context`: A special tool to set the active project for subsequent commands.
-   `clear_project_context`: To revert to the organization-level scope.

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
    -   Click **Create** and **copy the token immediately**. You will not be able to see it again.

2.  **Configure the MCP Server in Cline:**
    -   Open your `cline_mcp_settings.json` file.
    -   Add a new entry for the `mcp-azure-devops` server. The command should be `mcp-azure-devops`.

    Here is an example configuration:
    ```json
    {
      "mcpServers": {
        "mcp-azure-devops": {
          "command": "mcp-azure-devops",
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

## Acknowledgements

This project was inspired by the `mcp-atlassian` server, which provides similar functionality for Jira and Confluence. You can find it here: [https://github.com/pashpashpash/mcp-atlassian](https://github.com/pashpashpash/mcp-atlassian).
