#!/usr/bin/env python3
"""
MCP Azure DevOps Server Setup Validation Script

This script validates the setup and configuration of the MCP Azure DevOps server
to help diagnose common issues before they cause problems.
"""

import os
import sys
import subprocess
import json
from pathlib import Path
from typing import Dict, List, Tuple, Any

class SetupValidator:
    """Validates MCP Azure DevOps server setup and configuration."""
    
    def __init__(self):
        self.issues = []
        self.warnings = []
        self.info = []
        
    def log_issue(self, message: str):
        """Log a critical issue."""
        self.issues.append(f"❌ ISSUE: {message}")
        
    def log_warning(self, message: str):
        """Log a warning."""
        self.warnings.append(f"⚠️  WARNING: {message}")
        
    def log_info(self, message: str):
        """Log informational message."""
        self.info.append(f"ℹ️  INFO: {message}")
        
    def validate_python_version(self) -> bool:
        """Validate Python version is 3.10 or higher."""
        version = sys.version_info
        if version.major < 3 or (version.major == 3 and version.minor < 10):
            self.log_issue(f"Python version {version.major}.{version.minor} is not supported. Requires Python 3.10+")
            return False
        else:
            self.log_info(f"Python version {version.major}.{version.minor}.{version.micro} is supported")
            return True
    
    def validate_virtual_environment(self) -> bool:
        """Check if running in a virtual environment."""
        if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
            self.log_info("Running in virtual environment")
            return True
        else:
            self.log_warning("Not running in a virtual environment. Consider using 'python -m venv .venv'")
            return False
    
    def validate_dependencies(self) -> bool:
        """Validate required dependencies are installed."""
        required_packages = ['mcp', 'azure-devops']
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                self.log_info(f"Package '{package}' is installed")
            except ImportError:
                missing_packages.append(package)
                self.log_issue(f"Required package '{package}' is not installed")
        
        if missing_packages:
            self.log_issue(f"Install missing packages with: pip install {' '.join(missing_packages)}")
            return False
        
        return True
    
    def validate_environment_variables(self) -> bool:
        """Validate required environment variables."""
        required_vars = {
            'AZURE_DEVOPS_ORG_URL': 'Azure DevOps organization URL (e.g., https://dev.azure.com/your-org)',
            'AZURE_DEVOPS_PAT': 'Personal Access Token for Azure DevOps'
        }
        
        missing_vars = []
        for var, description in required_vars.items():
            value = os.getenv(var)
            if not value:
                missing_vars.append(var)
                self.log_issue(f"Missing environment variable: {var} ({description})")
            else:
                # Mask PAT for security
                display_value = value if var != 'AZURE_DEVOPS_PAT' else f"{value[:8]}...{value[-4:]}"
                self.log_info(f"Environment variable {var} is set: {display_value}")
        
        return len(missing_vars) == 0
    
    def validate_azure_devops_connection(self) -> bool:
        """Test Azure DevOps connection."""
        try:
            from mcp_azure_devops.azure_devops_client import AzureDevOpsClient
            
            client = AzureDevOpsClient()
            projects = client.get_projects()
            
            self.log_info(f"Successfully connected to Azure DevOps. Found {len(projects)} projects:")
            for project in projects[:5]:  # Show first 5 projects
                self.log_info(f"  - {project.name}")
            
            if len(projects) > 5:
                self.log_info(f"  ... and {len(projects) - 5} more projects")
            
            return True
            
        except Exception as e:
            self.log_issue(f"Failed to connect to Azure DevOps: {str(e)}")
            return False
    
    def validate_mcp_server_executable(self) -> bool:
        """Validate the MCP server executable exists and is accessible."""
        try:
            # Try to find the executable
            result = subprocess.run([sys.executable, '-m', 'mcp_azure_devops.server', '--help'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode == 0:
                self.log_info("MCP server executable is accessible")
                return True
            else:
                self.log_issue("MCP server executable failed to run")
                return False
                
        except subprocess.TimeoutExpired:
            self.log_warning("MCP server executable test timed out")
            return False
        except Exception as e:
            self.log_issue(f"Failed to test MCP server executable: {str(e)}")
            return False
    
    def validate_mcp_server_tools(self) -> bool:
        """Test that the MCP server can list its tools."""
        try:
            from mcp_azure_devops.server import MCPAzureDevOpsServer
            
            server = MCPAzureDevOpsServer()
            tools_count = len(server.tools)
            
            self.log_info(f"MCP server defines {tools_count} tools")
            
            # List some key tools
            key_tools = ['create_work_item', 'get_work_item', 'create_wiki_page', 'server_health_check']
            found_tools = [tool.name for tool in server.tools if tool.name in key_tools]
            
            for tool in found_tools:
                self.log_info(f"  ✓ {tool}")
            
            missing_tools = set(key_tools) - set(found_tools)
            for tool in missing_tools:
                self.log_warning(f"  ✗ {tool} (not found)")
            
            return tools_count > 0
            
        except Exception as e:
            self.log_issue(f"Failed to validate MCP server tools: {str(e)}")
            return False
    
    def find_cline_config_files(self) -> List[Path]:
        """Find potential Cline MCP configuration files."""
        possible_paths = [
            Path.home() / "AppData" / "Roaming" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
            Path.home() / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
            Path.home() / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
        ]
        
        found_files = []
        for path in possible_paths:
            if path.exists():
                found_files.append(path)
        
        return found_files
    
    def validate_cline_configuration(self) -> bool:
        """Validate Cline MCP configuration."""
        config_files = self.find_cline_config_files()
        
        if not config_files:
            self.log_warning("No Cline MCP configuration files found")
            self.log_info("Expected location (Windows): %APPDATA%\\Code\\User\\globalStorage\\saoudrizwan.claude-dev\\settings\\cline_mcp_settings.json")
            return False
        
        for config_file in config_files:
            self.log_info(f"Found Cline config: {config_file}")
            
            try:
                with open(config_file, 'r') as f:
                    config = json.load(f)
                
                if 'mcpServers' not in config:
                    self.log_warning(f"No mcpServers section in {config_file}")
                    continue
                
                if 'mcp-azure-devops' not in config['mcpServers']:
                    self.log_warning(f"No mcp-azure-devops server configured in {config_file}")
                    continue
                
                server_config = config['mcpServers']['mcp-azure-devops']
                
                # Check command path
                command = server_config.get('command', '')
                if not command:
                    self.log_issue(f"No command specified for mcp-azure-devops in {config_file}")
                elif not Path(command).exists():
                    self.log_issue(f"Command path does not exist: {command}")
                else:
                    self.log_info(f"Command path exists: {command}")
                
                # Check environment variables
                env = server_config.get('env', {})
                required_env_vars = ['AZURE_DEVOPS_ORG_URL', 'AZURE_DEVOPS_PAT']
                
                for var in required_env_vars:
                    if var not in env:
                        self.log_issue(f"Missing {var} in server environment configuration")
                    else:
                        display_value = env[var] if var != 'AZURE_DEVOPS_PAT' else f"{env[var][:8]}...{env[var][-4:]}"
                        self.log_info(f"Environment variable {var} configured: {display_value}")
                
                # Check if disabled
                if server_config.get('disabled', False):
                    self.log_warning("mcp-azure-devops server is disabled in configuration")
                else:
                    self.log_info("mcp-azure-devops server is enabled")
                
                return True
                
            except Exception as e:
                self.log_issue(f"Failed to parse config file {config_file}: {str(e)}")
        
        return False
    
    def generate_sample_config(self) -> str:
        """Generate a sample Cline configuration."""
        venv_path = Path(sys.prefix)
        if sys.platform == "win32":
            executable_path = venv_path / "Scripts" / "mcp-azure-devops.exe"
        else:
            executable_path = venv_path / "bin" / "mcp-azure-devops"
        
        sample_config = {
            "mcpServers": {
                "mcp-azure-devops": {
                    "command": str(executable_path),
                    "args": [],
                    "env": {
                        "AZURE_DEVOPS_ORG_URL": "https://dev.azure.com/your-organization",
                        "AZURE_DEVOPS_PAT": "your-personal-access-token"
                    },
                    "disabled": False,
                    "autoApprove": []
                }
            }
        }
        
        return json.dumps(sample_config, indent=2)
    
    def run_validation(self) -> bool:
        """Run all validation checks."""
        print("🔍 MCP Azure DevOps Server Setup Validation")
        print("=" * 50)
        
        checks = [
            ("Python Version", self.validate_python_version),
            ("Virtual Environment", self.validate_virtual_environment),
            ("Dependencies", self.validate_dependencies),
            ("Environment Variables", self.validate_environment_variables),
            ("Azure DevOps Connection", self.validate_azure_devops_connection),
            ("MCP Server Executable", self.validate_mcp_server_executable),
            ("MCP Server Tools", self.validate_mcp_server_tools),
            ("Cline Configuration", self.validate_cline_configuration),
        ]
        
        results = {}
        for check_name, check_func in checks:
            print(f"\n🔍 Checking {check_name}...")
            try:
                results[check_name] = check_func()
            except Exception as e:
                self.log_issue(f"Validation check '{check_name}' failed with error: {str(e)}")
                results[check_name] = False
        
        # Print results
        print("\n" + "=" * 50)
        print("📋 VALIDATION RESULTS")
        print("=" * 50)
        
        # Print issues
        if self.issues:
            print("\n❌ CRITICAL ISSUES:")
            for issue in self.issues:
                print(f"  {issue}")
        
        # Print warnings
        if self.warnings:
            print("\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        # Print info
        if self.info:
            print("\n✅ SUCCESS:")
            for info in self.info:
                print(f"  {info}")
        
        # Overall status
        has_critical_issues = len(self.issues) > 0
        print(f"\n{'=' * 50}")
        
        if has_critical_issues:
            print("❌ VALIDATION FAILED - Critical issues found")
            print("\n📝 SAMPLE CONFIGURATION:")
            print("Add this to your cline_mcp_settings.json file:")
            print("-" * 40)
            print(self.generate_sample_config())
            return False
        else:
            print("✅ VALIDATION PASSED - Setup looks good!")
            if self.warnings:
                print("⚠️  Some warnings were found, but they shouldn't prevent the server from working.")
            return True

def main():
    """Main entry point."""
    validator = SetupValidator()
    success = validator.run_validation()
    
    if not success:
        print("\n🔧 NEXT STEPS:")
        print("1. Fix the critical issues listed above")
        print("2. Restart VS Code/Cline after making changes")
        print("3. Run this validation script again")
        print("4. Check the MCP server logs for additional details")
        
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
