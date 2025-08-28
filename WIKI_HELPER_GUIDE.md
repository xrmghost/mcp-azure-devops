# Wiki Helper Methods Guide

This guide explains how to use the enhanced wiki helper methods in the Azure DevOps MCP server to solve common wiki management challenges.

## Overview of Problems Solved

The new wiki helper methods address three main issues:

1. **Update Failures**: Version conflicts when updating wiki pages
2. **Navigation Difficulties**: Hard to find wikis and pages without exact identifiers
3. **Limited Discovery**: Lack of search and suggestion capabilities

## New Helper Methods

### 1. Safe Update Methods

#### `update_wiki_page_safe`
Safely updates a wiki page with automatic retry on version conflicts.

**Usage:**
```json
{
  "project": "MyProject",
  "wiki_identifier": "MyWiki",
  "path": "/Documentation/API-Guide",
  "content": "# Updated API Guide\n\nThis is the updated content...",
  "max_retries": 3
}
```

**Benefits:**
- Automatically retries on version conflicts
- Eliminates most update failures
- Configurable retry attempts

#### `create_or_update_wiki_page_smart`
Creates a new wiki page or updates existing one intelligently.

**Usage:**
```json
{
  "project": "MyProject",
  "wiki_identifier": "MyWiki",
  "path": "/Documentation/New-Feature",
  "content": "# New Feature Documentation\n\nThis page will be created or updated..."
}
```

**Benefits:**
- No need to check if page exists first
- Handles both creation and updates seamlessly
- Reduces API calls

### 2. Discovery and Navigation Methods

#### `search_wiki_pages`
Search for wiki pages by title or content.

**Usage:**
```json
{
  "project": "MyProject",
  "wiki_identifier": "MyWiki",
  "search_term": "API authentication"
}
```

**Returns:**
```json
[
  {
    "path": "/Documentation/API-Guide",
    "url": "https://dev.azure.com/...",
    "content_preview": "# API Guide\n\nThis guide covers API authentication methods..."
  }
]
```

#### `get_wiki_page_tree`
Get hierarchical structure of wiki pages.

**Usage:**
```json
{
  "project": "MyProject",
  "wiki_identifier": "MyWiki"
}
```

**Returns:**
```json
{
  "Documentation": {
    "children": {
      "API-Guide": {
        "children": {},
        "info": {
          "path": "/Documentation/API-Guide",
          "url": "https://dev.azure.com/..."
        }
      }
    },
    "info": null
  }
}
```

#### `find_wiki_by_name`
Find wikis by partial name match.

**Usage:**
```json
{
  "project": "MyProject",
  "partial_name": "doc"
}
```

**Returns:**
```json
[
  {
    "id": "wiki-id",
    "name": "Documentation",
    "url": "https://dev.azure.com/...",
    "remote_url": "https://..."
  }
]
```

#### `get_wiki_page_by_title`
Find wiki page by title instead of exact path.

**Usage:**
```json
{
  "project": "MyProject",
  "wiki_identifier": "MyWiki",
  "title": "API Guide"
}
```

**Benefits:**
- No need to know exact path
- Fuzzy matching on titles
- Returns full page content

### 3. Organization-Wide Methods

#### `list_all_wikis_in_organization`
List all wikis across all projects in the organization.

**Usage:**
```json
{}
```

**Returns:**
```json
[
  {
    "project": "Project1",
    "id": "wiki-id-1",
    "name": "Documentation",
    "url": "https://dev.azure.com/...",
    "remote_url": "https://..."
  },
  {
    "project": "Project2",
    "id": "wiki-id-2",
    "name": "Knowledge Base",
    "url": "https://dev.azure.com/...",
    "remote_url": "https://..."
  }
]
```

### 4. Activity and Suggestion Methods

#### `get_recent_wiki_pages`
Get recently modified wiki pages.

**Usage:**
```json
{
  "project": "MyProject",
  "wiki_identifier": "MyWiki",
  "limit": 5
}
```

#### `get_wiki_page_suggestions`
Get page suggestions based on partial input.

**Usage:**
```json
{
  "project": "MyProject",
  "wiki_identifier": "MyWiki",
  "partial_input": "api"
}
```

**Returns:**
```json
[
  {
    "path": "/Documentation/API-Guide",
    "url": "https://dev.azure.com/...",
    "match_score": 100
  },
  {
    "path": "/Tutorials/API-Examples",
    "url": "https://dev.azure.com/...",
    "match_score": 50
  }
]
```

### 5. Batch Operations

#### `create_wiki_pages_batch`
Create multiple wiki pages at once.

**Usage:**
```json
{
  "project": "MyProject",
  "wiki_identifier": "MyWiki",
  "pages_data": [
    {
      "path": "/Documentation/Getting-Started",
      "content": "# Getting Started\n\nWelcome to our documentation..."
    },
    {
      "path": "/Documentation/FAQ",
      "content": "# Frequently Asked Questions\n\nQ: How do I..."
    }
  ]
}
```

**Returns:**
```json
[
  {
    "path": "/Documentation/Getting-Started",
    "status": "success",
    "result": { ... }
  },
  {
    "path": "/Documentation/FAQ",
    "status": "success",
    "result": { ... }
  }
]
```

## Common Usage Patterns

### Pattern 1: Safe Page Updates
Instead of using `update_wiki_page` which can fail on version conflicts:

```
1. Use `update_wiki_page_safe` for reliable updates
2. Or use `create_or_update_wiki_page_smart` if you're unsure if the page exists
```

### Pattern 2: Finding Pages Without Exact Paths
Instead of needing to know exact paths:

```
1. Use `search_wiki_pages` to find pages by content
2. Use `get_wiki_page_by_title` to find by title
3. Use `get_wiki_page_suggestions` for autocomplete-like functionality
```

### Pattern 3: Exploring Wiki Structure
To understand the organization of a wiki:

```
1. Use `get_wiki_page_tree` to see the hierarchical structure
2. Use `list_wiki_pages` for a flat list
3. Use `get_recent_wiki_pages` to see what's been active
```

### Pattern 4: Cross-Project Wiki Discovery
To find wikis across your organization:

```
1. Use `list_all_wikis_in_organization` to see all wikis
2. Use `find_wiki_by_name` to find wikis by partial name
```

## Migration from Original Methods

### Before (Problematic)
```json
// This could fail with version conflicts
{
  "tool": "update_wiki_page",
  "arguments": {
    "project": "MyProject",
    "wiki_identifier": "MyWiki",
    "path": "/exact/path/required",
    "content": "Updated content"
  }
}
```

### After (Reliable)
```json
// This will retry automatically on conflicts
{
  "tool": "update_wiki_page_safe",
  "arguments": {
    "project": "MyProject",
    "wiki_identifier": "MyWiki",
    "path": "/exact/path/required",
    "content": "Updated content"
  }
}
```

### Or Even Better (Smart)
```json
// This will create or update as needed
{
  "tool": "create_or_update_wiki_page_smart",
  "arguments": {
    "project": "MyProject",
    "wiki_identifier": "MyWiki",
    "path": "/Documentation/Feature-Guide",
    "content": "Updated content"
  }
}
```

## Error Handling

The new methods provide better error messages and handling:

- **Version Conflicts**: Automatically retried with fresh versions
- **Page Not Found**: Clear messages with suggestions
- **Permission Issues**: Detailed error information
- **Batch Operations**: Individual success/failure status for each item

## Best Practices

1. **Use Safe Methods**: Prefer `update_wiki_page_safe` over `update_wiki_page`
2. **Use Smart Methods**: Use `create_or_update_wiki_page_smart` when unsure if page exists
3. **Leverage Search**: Use search methods instead of guessing exact paths
4. **Batch When Possible**: Use batch operations for multiple page creation
5. **Explore Structure**: Use tree and suggestion methods to understand wiki organization

## Backward Compatibility

All original wiki methods remain available and unchanged:
- `create_wiki_page`
- `get_wiki_page`
- `update_wiki_page`
- `delete_wiki_page`
- `list_wiki_pages`
- `get_wikis`
- `create_wiki`

The new methods are additions that enhance the existing functionality without breaking existing integrations.
