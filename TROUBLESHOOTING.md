# MCP Azure DevOps Server Troubleshooting Guide

This guide helps you diagnose and fix common issues with the MCP Azure DevOps server.

## Quick Diagnosis

First, run the validation script to identify issues:

```bash
python validate_setup.py
```

This script will check your entire setup and provide specific guidance on any problems found.

## Common Issues and Solutions

### 1. "No tools found" in VS Code MCP Servers

**Symptoms:**
- VS Code shows the server as connected but displays "No tools found"
- LLMs cannot see or use any Azure DevOps tools

**Causes and Solutions:**

#### A. MCP Protocol Communication Issues
```bash
# Check if the server starts correctly
python -m mcp_azure_devops.server

# Look for these log messages:
# - "Starting MCP Azure DevOps Server..."
# - "Server initialization completed successfully"
# - "Registered X tools"
```

#### B. Environment Variables Not Set
The server requires these environment variables:
- `AZURE_DEVOPS_ORG_URL`: Your Azure DevOps organization URL
- `AZURE_DEVOPS_PAT`: Your Personal Access Token

**Fix:**
1. Set environment variables in your Cline configuration
2. Restart VS Code/Cline after making changes

#### C. Incorrect Cline Configuration
Check your `cline_mcp_settings.json` file:

```json
{
  "mcpServers": {
    "mcp-azure-devops": {
      "command": "C:\\full\\path\\to\\.venv\\Scripts\\mcp-azure-devops.exe",
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

**Common mistakes:**
- Using relative paths instead of absolute paths
- Missing environment variables in the `env` section
- Server marked as `"disabled": true`

### 2. Server Fails to Start

**Symptoms:**
- Server immediately exits or crashes
- Error messages in logs about missing dependencies or configuration

**Solutions:**

#### A. Missing Dependencies
```bash
pip install -e .
```

#### B. Python Version Issues
Ensure you're using Python 3.10 or higher:
```bash
python --version
```

#### C. Virtual Environment Issues
Make sure you're in the correct virtual environment:
```bash
# Windows
.\.venv\Scripts\activate

# macOS/Linux
source .venv/bin/activate
```

### 3. Azure DevOps Connection Failures

**Symptoms:**
- "Failed to connect to Azure DevOps" errors
- Authentication failures
- Network timeout errors

**Solutions:**

#### A. Verify Personal Access Token (PAT)
1. Go to Azure DevOps → User Settings → Personal Access Tokens
2. Ensure your token has these permissions:
   - **Work Items:** Read & write
   - **Wiki:** Read & write
   - **Code:** Read
   - **Graph:** Read (for user listing)
3. Check token expiration date
4. Regenerate token if necessary

#### B. Verify Organization URL
Ensure your URL follows this format:
```
https://dev.azure.com/your-organization-name
```

#### C. Network/Firewall Issues
- Check if you can access Azure DevOps in your browser
- Verify corporate firewall settings
- Test with a different network if possible

### 4. Tool Execution Failures

**Symptoms:**
- Tools are visible but fail when executed
- Specific error messages about missing projects or permissions

**Solutions:**

#### A. Project Access Issues
```bash
# Test project access
python -c "
from mcp_azure_devops.azure_devops_client import AzureDevOpsClient
client = AzureDevOpsClient()
projects = client.get_projects()
print(f'Found {len(projects)} projects')
for p in projects[:5]:
    print(f'  - {p.name}')
"
```

#### B. Permission Issues
Verify your PAT has the required permissions for the operations you're trying to perform.

#### C. Project Context Issues
Use the `set_project_context` tool to set a default project:
```json
{
  "project": "YourProjectName"
}
```

### 5. Performance Issues

**Symptoms:**
- Slow tool responses
- Timeout errors
- High memory usage

**Solutions:**

#### A. Reduce Query Scope
- Use specific project names instead of organization-wide queries
- Limit search results with appropriate filters
- Use pagination for large result sets

#### B. Network Optimization
- Use a stable internet connection
- Consider Azure DevOps region proximity

### 6. Logging and Debugging

#### Enable Debug Logging
The server automatically logs to stderr. To capture logs:

```bash
# Run server with log capture
python -m mcp_azure_devops.server 2> server.log
```

#### Key Log Messages to Look For
- `"Starting MCP Azure DevOps Server..."`
- `"Server initialization completed successfully"`
- `"Registered X tools"`
- `"Tools requested - returning X tools"`
- `"Tool called: <tool_name>"`

#### Common Error Patterns
- `"Missing required environment variables"`: Environment setup issue
- `"Failed to initialize Azure DevOps client"`: Authentication/connection issue
- `"Tool 'X' not found"`: Server registration issue

## Advanced Troubleshooting

### Manual Server Testing

Test the server manually:

```python
import asyncio
from mcp_azure_devops.server import MCPAzureDevOpsServer

async def test_server():
    server = MCPAzureDevOpsServer()
    
    # Test tool listing
    tools = server.tools
    print(f"Server defines {len(tools)} tools")
    
    # Test health check
    health = await server._health_check()
    print(f"Health check: {health}")

asyncio.run(test_server())
```

### MCP Protocol Testing

Test MCP protocol communication:

```bash
# Test with MCP inspector (if available)
npx @modelcontextprotocol/inspector python -m mcp_azure_devops.server
```

### Configuration File Locations

Common locations for `cline_mcp_settings.json`:

**Windows:**
```
%APPDATA%\Code\User\globalStorage\saoudrizwan.claude-dev\settings\cline_mcp_settings.json
```

**macOS:**
```
~/Library/Application Support/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
```

**Linux:**
```
~/.config/Code/User/globalStorage/saoudrizwan.claude-dev/settings/cline_mcp_settings.json
```

## Getting Help

If you're still experiencing issues:

1. **Run the validation script:** `python validate_setup.py`
2. **Check the logs:** Look for error messages in the server output
3. **Test individual components:** Use the manual testing scripts above
4. **Create an issue:** Include validation script output and relevant logs

## Health Check Tool

Use the built-in health check tool to verify server status:

```json
{
  "tool": "server_health_check",
  "arguments": {}
}
```

This will return comprehensive status information about:
- Server initialization
- Environment configuration
- Azure DevOps connectivity
- Tool registration status
- Available projects

## Prevention Tips

1. **Always use absolute paths** in Cline configuration
2. **Set environment variables** in the server configuration, not globally
3. **Use virtual environments** to avoid dependency conflicts
4. **Regularly validate your setup** with the validation script
5. **Keep your PAT updated** and monitor expiration dates
6. **Test changes incrementally** rather than making multiple changes at once
