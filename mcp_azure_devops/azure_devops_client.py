import os
from msrest.authentication import BasicAuthentication
from azure.devops.connection import Connection
from azure.devops.v7_1.work_item_tracking.models import JsonPatchOperation, Wiql
from azure.devops.v7_1.wiki.models import WikiCreateParametersV2, WikiPagesBatchRequest
from azure.devops.v7_1.graph.graph_client import GraphClient

# Default fields to format as markdown for better LLM readability
DEFAULT_MARKDOWN_FIELDS = [
    "System.Description",
    "System.History",
    "Microsoft.VSTS.TCM.ReproSteps",
    "Microsoft.VSTS.TCM.SystemInfo",
    "Microsoft.VSTS.Common.AcceptanceCriteria"
]

class AzureDevOpsClient:
    def __init__(self):
        self.org_url = os.getenv("AZURE_DEVOPS_ORG_URL")
        self.pat = os.getenv("AZURE_DEVOPS_PAT")
        self.project_context = None
        
        if not self.org_url or not self.pat:
            raise ValueError("AZURE_DEVOPS_ORG_URL and AZURE_DEVOPS_PAT environment variables must be set.")
            
        self.credentials = BasicAuthentication('', self.pat)
        self.connection = Connection(base_url=self.org_url, creds=self.credentials)
        
        # Initialize clients lazily to avoid connection issues during server startup
        self._core_client = None
        self._work_item_tracking_client = None
        self._wiki_client = None
        self._git_client = None
        self._graph_client = None

    @property
    def core_client(self):
        if self._core_client is None:
            self._core_client = self.connection.clients.get_core_client()
        return self._core_client

    @property
    def work_item_tracking_client(self):
        if self._work_item_tracking_client is None:
            self._work_item_tracking_client = self.connection.clients.get_work_item_tracking_client()
        return self._work_item_tracking_client

    @property
    def wiki_client(self):
        if self._wiki_client is None:
            self._wiki_client = self.connection.clients.get_wiki_client()
        return self._wiki_client

    @property
    def git_client(self):
        if self._git_client is None:
            self._git_client = self.connection.clients.get_git_client()
        return self._git_client

    @property
    def graph_client(self):
        if self._graph_client is None:
            self._graph_client = self.connection.clients.get_graph_client()
        return self._graph_client

    @property
    def work_client(self):
        if not hasattr(self, '_work_client') or self._work_client is None:
            self._work_client = self.connection.clients.get_work_client()
        return self._work_client

    def list_users(self):
        return self.graph_client.list_users()

    def set_project_context(self, project):
        self.project_context = project
        return {"message": f"Project context set to '{project}'."}

    def clear_project_context(self):
        self.project_context = None
        return {"message": "Project context cleared."}

    def get_projects(self):
        return self.core_client.get_projects()

    def _add_markdown_format_operations(self, patch_document, fields_dict, markdown_fields=None):
        """
        Adds multilineFieldsFormat operations for markdown fields.
        This enables better LLM readability by storing multiline text as markdown instead of HTML.
        
        Args:
            patch_document: List of JsonPatchOperation to append to
            fields_dict: Dict of field reference names and their values being set
            markdown_fields: Optional list of additional field reference names to format as markdown
        """
        # Combine default markdown fields with any additional fields specified
        all_markdown_fields = set(DEFAULT_MARKDOWN_FIELDS)
        if markdown_fields:
            all_markdown_fields.update(markdown_fields)
        
        # Add format operation for each field that should be markdown
        for field_name in fields_dict.keys():
            if field_name in all_markdown_fields:
                patch_document.append(
                    JsonPatchOperation(
                        op="add",
                        path=f"/multilineFieldsFormat/{field_name}",
                        value="markdown"
                    )
                )

    def create_work_item(self, project, work_item_type, title, description, custom_fields=None, relations=None, markdown_fields=None):
        """
        Creates a new work item in Azure DevOps.
        
        Args:
            project: Project name or ID
            work_item_type: Type of work item (e.g., 'Bug', 'User Story', 'Task')
            title: Work item title
            description: Work item description
            custom_fields: Optional dict of additional field names and values
            relations: Optional list of relations to other work items
            markdown_fields: Optional list of additional field reference names to format as markdown.
                           System fields like System.Description are automatically formatted as markdown.
                           Use this to include custom multiline fields (e.g., ["Custom.Notes"]).
        
        Returns:
            Created work item object
        """
        # Build all fields that will be set
        all_fields = {
            "System.Title": title,
            "System.Description": description
        }
        if custom_fields:
            all_fields.update(custom_fields)
        
        # Create patch operations for all fields
        patch_document = []
        for field, value in all_fields.items():
            patch_document.append(
                JsonPatchOperation(
                    op="add",
                    path=f"/fields/{field}",
                    value=value
                )
            )
        
        # Add markdown format operations for multiline fields
        self._add_markdown_format_operations(patch_document, all_fields, markdown_fields)

        # Add relations if provided
        if relations:
            for relation in relations:
                patch_document.append(
                    JsonPatchOperation(
                        op="add",
                        path="/relations/-",
                        value={
                            "rel": relation["rel"],
                            "url": relation["url"]
                        }
                    )
                )
        
        return self.work_item_tracking_client.create_work_item(
            document=patch_document,
            project=project,
            type=work_item_type
        )

    def get_work_item(self, work_item_id, expand=None):
        work_item = self.work_item_tracking_client.get_work_item(id=work_item_id, expand=expand)
        result = {
            "id": work_item.id,
            "url": work_item.url,
            "fields": work_item.fields
        }
        if work_item.relations:
            result["relations"] = [
                {
                    "rel": r.rel,
                    "url": r.url,
                    "attributes": r.attributes
                } for r in work_item.relations
            ]
        
        # If expand includes "All", fetch and include history
        if expand and "All" in expand:
            try:
                updates = self.work_item_tracking_client.get_updates(id=work_item_id)
                
                # Handle multiple failure scenarios - check if updates is iterable
                if updates is not None and hasattr(updates, '__iter__') and not isinstance(updates, str):
                    try:
                        result["history"] = [
                            {
                                "id": update.id,
                                "rev": update.rev,
                                "revised_by": {
                                    "id": update.revised_by.id if update.revised_by else None,
                                    "display_name": update.revised_by.display_name if update.revised_by else None,
                                    "unique_name": update.revised_by.unique_name if update.revised_by else None
                                } if update.revised_by else None,
                                "revised_date": update.revised_date.isoformat() if update.revised_date else None,
                                "fields": update.fields if hasattr(update, 'fields') else {},
                                "relations": {
                                    "added": [{"rel": r.rel, "url": r.url} for r in update.relations.added] if hasattr(update, 'relations') and update.relations and hasattr(update.relations, 'added') else [],
                                    "removed": [{"rel": r.rel, "url": r.url} for r in update.relations.removed] if hasattr(update, 'relations') and update.relations and hasattr(update.relations, 'removed') else [],
                                    "updated": [{"rel": r.rel, "url": r.url} for r in update.relations.updated] if hasattr(update, 'relations') and update.relations and hasattr(update.relations, 'updated') else []
                                } if hasattr(update, 'relations') else None
                            }
                            for update in updates
                        ]
                    except TypeError:
                        # Fallback if iteration still fails
                        result["history"] = []
                else:
                    result["history"] = []
            except Exception as e:
                # Log but don't fail the entire request
                result["history_error"] = f"Failed to retrieve history: {str(e)}"
        
        return result

    def update_work_item(self, work_item_id, updates, relations=None, markdown_fields=None):
        """
        Updates an existing work item in Azure DevOps.
        
        Args:
            work_item_id: ID of the work item to update
            updates: Dict of field names and values to update
            relations: Optional list of relations to add
            markdown_fields: Optional list of additional field reference names to format as markdown.
                           System fields like System.Description are automatically formatted as markdown.
                           Use this to include custom multiline fields (e.g., ["Custom.Notes"]).
        
        Returns:
            Updated work item object
        """
        # Create patch operations for all field updates
        patch_document = []
        for field, value in updates.items():
            patch_document.append(
                JsonPatchOperation(
                    op="add",
                    path=f"/fields/{field}",
                    value=value
                )
            )
        
        # Add markdown format operations for multiline fields
        self._add_markdown_format_operations(patch_document, updates, markdown_fields)

        # Add relations if provided
        if relations:
            for relation in relations:
                patch_document.append(
                    JsonPatchOperation(
                        op="add",
                        path="/relations/-",
                        value={
                            "rel": relation["rel"],
                            "url": relation["url"]
                        }
                    )
                )
        
        return self.work_item_tracking_client.update_work_item(
            document=patch_document,
            id=work_item_id
        )

    def delete_work_item(self, work_item_id):
        return self.work_item_tracking_client.delete_work_item(id=work_item_id)

    def search_work_items(self, project, wiql_query):
        # Add project filter to the WIQL query if not already present
        if "[System.TeamProject]" not in wiql_query and "WHERE" in wiql_query.upper():
            # Insert project filter into existing WHERE clause
            wiql_query = wiql_query.replace(" WHERE ", f" WHERE [System.TeamProject] = '{project}' AND ")
        elif "[System.TeamProject]" not in wiql_query:
            # Add WHERE clause with project filter
            wiql_query += f" WHERE [System.TeamProject] = '{project}'"
        
        wiql = Wiql(query=wiql_query)
        # Call query_by_wiql without the project parameter
        query_result = self.work_item_tracking_client.query_by_wiql(wiql)
        
        if query_result.work_items:
            work_item_ids = [item.id for item in query_result.work_items]
            work_items = self.work_item_tracking_client.get_work_items(ids=work_item_ids)
            return [
                {
                    "id": wi.id,
                    "title": wi.fields.get("System.Title"),
                    "state": wi.fields.get("System.State"),
                    "url": wi.url,
                }
                for wi in work_items
            ]
        else:
            return []

    def get_work_item_comments(self, work_item_id, project=None, top=None, continuation_token=None, include_deleted=False, expand=None, order=None):
        """
        Get comments for a specific work item.
        
        Args:
            work_item_id (int): The ID of the work item to get comments for
            project (str, optional): Project name or ID. If not provided, uses project_context
            top (int, optional): Maximum number of comments to return (pagination)
            continuation_token (str, optional): Token for getting next page of results
            include_deleted (bool): Whether to include deleted comments (default: False)
            expand (str, optional): Additional data retrieval options for work item comments
            order (str, optional): Order in which comments should be returned
            
        Returns:
            dict: Contains comments list and pagination info
        """
        # Use provided project or fallback to context
        project_name = project or self.project_context
        if not project_name:
            raise ValueError("Project must be specified either as parameter or set in project context")
        
        # Get comments from Azure DevOps API
        comment_list = self.work_item_tracking_client.get_comments(
            project=project_name,
            work_item_id=work_item_id,
            top=top,
            continuation_token=continuation_token,
            include_deleted=include_deleted,
            expand=expand,
            order=order
        )
        
        # Format the response
        result = {
            "total_count": comment_list.total_count if hasattr(comment_list, 'total_count') else None,
            "continuation_token": comment_list.continuation_token if hasattr(comment_list, 'continuation_token') else None,
            "comments": []
        }
        
        if comment_list.comments:
            for comment in comment_list.comments:
                formatted_comment = {
                    "id": comment.id,
                    "text": comment.text,
                    "created_by": {
                        "id": comment.created_by.id if comment.created_by else None,
                        "display_name": comment.created_by.display_name if comment.created_by else None,
                        "unique_name": comment.created_by.unique_name if comment.created_by else None,
                        "image_url": comment.created_by.image_url if comment.created_by else None
                    } if comment.created_by else None,
                    "created_date": comment.created_date.isoformat() if comment.created_date else None,
                    "modified_by": {
                        "id": comment.modified_by.id if comment.modified_by else None,
                        "display_name": comment.modified_by.display_name if comment.modified_by else None,
                        "unique_name": comment.modified_by.unique_name if comment.modified_by else None,
                        "image_url": comment.modified_by.image_url if comment.modified_by else None
                    } if comment.modified_by else None,
                    "modified_date": comment.modified_date.isoformat() if comment.modified_date else None,
                    "url": comment.url if hasattr(comment, 'url') else None,
                    "version": comment.version if hasattr(comment, 'version') else None
                }
                result["comments"].append(formatted_comment)
        
        return result

    def add_work_item_comment(self, work_item_id, comment_text, project=None):
        """
        Add a comment to a work item.
        
        Args:
            work_item_id (int): The ID of the work item
            comment_text (str): The comment text to add
            project (str, optional): Project name or ID. Uses project_context if not provided
            
        Returns:
            dict: Created comment with id, text, created_by, created_date
        """
        from azure.devops.v7_1.work_item_tracking.models import CommentCreate
        
        # Use provided project or fallback to context
        project_name = project or self.project_context
        if not project_name:
            raise ValueError(
                "Project must be specified either as parameter or set via set_project_context tool. "
                "Use set_project_context to set the project context for subsequent commands."
            )
        
        # Create comment request
        comment_request = CommentCreate(text=comment_text)
        
        # Add comment via API
        comment = self.work_item_tracking_client.add_comment(
            project=project_name,
            work_item_id=work_item_id,
            request=comment_request
        )
        
        # Format response
        return {
            "id": comment.id,
            "work_item_id": work_item_id,
            "text": comment.text,
            "created_by": {
                "id": comment.created_by.id if comment.created_by else None,
                "display_name": comment.created_by.display_name if comment.created_by else None,
                "unique_name": comment.created_by.unique_name if comment.created_by else None
            } if comment.created_by else None,
            "created_date": comment.created_date.isoformat() if comment.created_date else None,
            "url": comment.url if hasattr(comment, 'url') else None
        }

    def get_work_item_history(self, work_item_id, project=None, top=None, skip=None):
        """
        Get revision history for a work item with pagination.
        
        Args:
            work_item_id (int): The ID of the work item
            project (str, optional): Project name or ID. Uses project_context if not provided
            top (int, optional): Maximum number of revisions to return
            skip (int, optional): Number of revisions to skip (for pagination)
            
        Returns:
            dict: Revision history with updates list and pagination info
        """
        # Use provided project or fallback to context (not strictly required by SDK but good for consistency)
        project_name = project or self.project_context
        
        # Get updates from API
        updates = self.work_item_tracking_client.get_updates(
            id=work_item_id,
            top=top,
            skip=skip
        )
        
        # Format response
        result = {
            "work_item_id": work_item_id,
            "total_updates": 0,
            "updates": []
        }
        
        # Handle multiple failure scenarios - check if updates is iterable
        if updates is not None and hasattr(updates, '__iter__') and not isinstance(updates, str):
            try:
                result["total_updates"] = len(updates)
                for update in updates:
                    formatted_update = {
                        "id": update.id,
                        "rev": update.rev,
                        "revised_by": {
                            "id": update.revised_by.id if update.revised_by else None,
                            "display_name": update.revised_by.display_name if update.revised_by else None,
                            "unique_name": update.revised_by.unique_name if update.revised_by else None,
                            "image_url": update.revised_by.image_url if update.revised_by and hasattr(update.revised_by, 'image_url') else None
                        } if update.revised_by else None,
                        "revised_date": update.revised_date.isoformat() if update.revised_date else None,
                        "fields": update.fields if hasattr(update, 'fields') else {},
                        "relations": {
                            "added": [{"rel": r.rel, "url": r.url, "attributes": r.attributes if hasattr(r, 'attributes') else {}} for r in update.relations.added] if hasattr(update, 'relations') and update.relations and hasattr(update.relations, 'added') else [],
                            "removed": [{"rel": r.rel, "url": r.url, "attributes": r.attributes if hasattr(r, 'attributes') else {}} for r in update.relations.removed] if hasattr(update, 'relations') and update.relations and hasattr(update.relations, 'removed') else [],
                            "updated": [{"rel": r.rel, "url": r.url, "attributes": r.attributes if hasattr(r, 'attributes') else {}} for r in update.relations.updated] if hasattr(update, 'relations') and update.relations and hasattr(update.relations, 'updated') else []
                        } if hasattr(update, 'relations') else None,
                        "url": update.url if hasattr(update, 'url') else None
                    }
                    result["updates"].append(formatted_update)
            except TypeError:
                # Fallback if iteration still fails
                pass
        
        return result

    def create_wiki_page(self, project, wiki_identifier, path, content):
        parameters = {
            "content": content
        }
        return self.wiki_client.create_or_update_page(
            project=project,
            wiki_identifier=wiki_identifier,
            path=path,
            parameters=parameters,
            version=None
        )

    def get_wiki_page(self, project, wiki_identifier, path):
        return self.wiki_client.get_page(
            project=project,
            wiki_identifier=wiki_identifier,
            path=path,
            include_content=True
        )

    def update_wiki_page(self, project, wiki_identifier, path, content):
        page = self.wiki_client.get_page(
            project=project,
            wiki_identifier=wiki_identifier,
            path=path
        )
        
        # Try to get ETag from various possible locations
        etag = None
        if hasattr(page, 'eTag'):
            etag = page.eTag
        elif hasattr(page, 'etag'):
            etag = page.etag
        elif hasattr(page, 'e_tag'):
            etag = page.e_tag
        elif hasattr(page, '_etag'):
            etag = page._etag
        elif hasattr(page, 'page') and hasattr(page.page, 'eTag'):
            etag = page.page.eTag
        elif hasattr(page, 'page') and hasattr(page.page, 'etag'):
            etag = page.page.etag
        elif hasattr(page, 'page') and hasattr(page.page, 'e_tag'):
            etag = page.page.e_tag
        
        parameters = {
            "content": content
        }
        return self.wiki_client.create_or_update_page(
            project=project,
            wiki_identifier=wiki_identifier,
            path=path,
            parameters=parameters,
            version=etag
        )

    def update_wiki_page_safe(self, project, wiki_identifier, path, content, max_retries=3):
        """
        Safely updates a wiki page with automatic retry on version conflicts.
        """
        for attempt in range(max_retries):
            try:
                # Get the latest version of the page
                page = self.wiki_client.get_page(
                    project=project,
                    wiki_identifier=wiki_identifier,
                    path=path
                )
                
                # Try to get ETag from various possible locations
                etag = None
                if hasattr(page, 'eTag'):
                    etag = page.eTag
                elif hasattr(page, 'etag'):
                    etag = page.etag
                elif hasattr(page, 'e_tag'):
                    etag = page.e_tag
                elif hasattr(page, '_etag'):
                    etag = page._etag
                elif hasattr(page, 'page') and hasattr(page.page, 'eTag'):
                    etag = page.page.eTag
                elif hasattr(page, 'page') and hasattr(page.page, 'etag'):
                    etag = page.page.etag
                elif hasattr(page, 'page') and hasattr(page.page, 'e_tag'):
                    etag = page.page.e_tag
                
                parameters = {
                    "content": content
                }
                return self.wiki_client.create_or_update_page(
                    project=project,
                    wiki_identifier=wiki_identifier,
                    path=path,
                    parameters=parameters,
                    version=etag
                )
            except Exception as e:
                if "version" in str(e).lower() and attempt < max_retries - 1:
                    # Version conflict, retry with fresh version
                    continue
                else:
                    raise e
        
        raise Exception(f"Failed to update wiki page after {max_retries} attempts due to version conflicts")

    def create_or_update_wiki_page_smart(self, project, wiki_identifier, path, content):
        """
        Creates a new wiki page or updates existing one intelligently.
        """
        try:
            # Try to update first
            return self.update_wiki_page_safe(project, wiki_identifier, path, content)
        except Exception as e:
            if "not found" in str(e).lower() or "404" in str(e):
                # Page doesn't exist, create it
                return self.create_wiki_page(project, wiki_identifier, path, content)
            else:
                raise e

    def search_wiki_pages(self, project, wiki_identifier, search_term):
        """
        Search for wiki pages by title or content.
        """
        pages = self.list_wiki_pages(project, wiki_identifier)
        matching_pages = []
        
        for page_info in pages:
            try:
                # Get page content to search in
                page = self.wiki_client.get_page(
                    project=project,
                    wiki_identifier=wiki_identifier,
                    path=page_info["path"],
                    include_content=True
                )
                
                # Search in path (title) and content
                if (search_term.lower() in page_info["path"].lower() or 
                    (page.page.content and search_term.lower() in page.page.content.lower())):
                    matching_pages.append({
                        "path": page_info["path"],
                        "url": page_info["url"],
                        "content_preview": page.page.content[:200] + "..." if page.page.content and len(page.page.content) > 200 else page.page.content
                    })
            except Exception:
                # Skip pages that can't be accessed
                continue
                
        return matching_pages

    def get_wiki_page_tree(self, project, wiki_identifier):
        """
        Get hierarchical structure of wiki pages.
        """
        pages = self.list_wiki_pages(project, wiki_identifier)
        
        # Organize pages into a tree structure
        tree = {}
        for page in pages:
            path_parts = page["path"].strip("/").split("/")
            current_level = tree
            
            for i, part in enumerate(path_parts):
                if part not in current_level:
                    current_level[part] = {
                        "children": {},
                        "info": None
                    }
                
                if i == len(path_parts) - 1:
                    # This is the final part, store page info
                    current_level[part]["info"] = page
                
                current_level = current_level[part]["children"]
        
        return tree

    def find_wiki_by_name(self, project, partial_name):
        """
        Find wikis by partial name match.
        """
        wikis = self.get_wikis(project)
        matching_wikis = []
        
        for wiki in wikis:
            if partial_name.lower() in wiki.name.lower():
                matching_wikis.append({
                    "id": wiki.id,
                    "name": wiki.name,
                    "url": wiki.url,
                    "remote_url": wiki.remote_url,
                })
        
        return matching_wikis

    def get_wiki_page_by_title(self, project, wiki_identifier, title):
        """
        Find wiki page by title instead of exact path.
        """
        pages = self.list_wiki_pages(project, wiki_identifier)
        
        for page in pages:
            # Extract title from path (last part after /)
            page_title = page["path"].split("/")[-1].replace("-", " ").replace("_", " ")
            if title.lower() in page_title.lower() or page_title.lower() in title.lower():
                try:
                    full_page = self.get_wiki_page(project, wiki_identifier, page["path"])
                    return full_page
                except Exception:
                    continue
        
        return None

    def list_all_wikis_in_organization(self):
        """
        List all wikis across all projects in the organization.
        """
        projects = self.get_projects()
        all_wikis = []
        
        for project in projects:
            try:
                wikis = self.get_wikis(project.name)
                for wiki in wikis:
                    all_wikis.append({
                        "project": project.name,
                        "id": wiki.id,
                        "name": wiki.name,
                        "url": wiki.url,
                        "remote_url": wiki.remote_url,
                    })
            except Exception:
                # Skip projects where we can't access wikis
                continue
        
        return all_wikis

    def get_recent_wiki_pages(self, project, wiki_identifier, limit=10):
        """
        Get recently modified wiki pages.
        """
        pages = self.list_wiki_pages(project, wiki_identifier)
        
        # Sort by view stats if available (proxy for recent activity)
        pages_with_activity = []
        for page in pages:
            if page.get("view_stats"):
                latest_activity = max(page["view_stats"], key=lambda x: x["date"]) if page["view_stats"] else None
                pages_with_activity.append({
                    **page,
                    "latest_activity": latest_activity
                })
            else:
                pages_with_activity.append({
                    **page,
                    "latest_activity": None
                })
        
        # Sort by latest activity date
        pages_with_activity.sort(
            key=lambda x: x["latest_activity"]["date"] if x["latest_activity"] else "1900-01-01",
            reverse=True
        )
        
        return pages_with_activity[:limit]

    def get_wiki_page_suggestions(self, project, wiki_identifier, partial_input):
        """
        Get page suggestions based on partial input.
        """
        pages = self.list_wiki_pages(project, wiki_identifier)
        suggestions = []
        
        for page in pages:
            path_lower = page["path"].lower()
            input_lower = partial_input.lower()
            
            # Score based on how well the input matches
            score = 0
            if path_lower.startswith(input_lower):
                score = 100  # Exact prefix match
            elif input_lower in path_lower:
                score = 50   # Contains match
            elif any(part.startswith(input_lower) for part in path_lower.split("/")):
                score = 25   # Part starts with input
            
            if score > 0:
                suggestions.append({
                    **page,
                    "match_score": score
                })
        
        # Sort by score and return top suggestions
        suggestions.sort(key=lambda x: x["match_score"], reverse=True)
        return suggestions[:10]

    def create_wiki_pages_batch(self, project, wiki_identifier, pages_data):
        """
        Create multiple wiki pages at once.
        pages_data: list of {"path": str, "content": str}
        """
        results = []
        for page_data in pages_data:
            try:
                result = self.create_wiki_page(
                    project=project,
                    wiki_identifier=wiki_identifier,
                    path=page_data["path"],
                    content=page_data["content"]
                )
                results.append({
                    "path": page_data["path"],
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                results.append({
                    "path": page_data["path"],
                    "status": "error",
                    "error": str(e)
                })
        
        return results

    def delete_wiki_page(self, project, wiki_identifier, path):
        return self.wiki_client.delete_page(
            project=project,
            wiki_identifier=wiki_identifier,
            path=path
        )

    def move_wiki_page(self, project, wiki_identifier, from_path, to_path):
        """
        Move a wiki page from one location to another atomically.
        This involves getting the source content, creating at target, and deleting original.
        """
        try:
            # Step 1: Get the source page content
            source_page = self.wiki_client.get_page(
                project=project,
                wiki_identifier=wiki_identifier,
                path=from_path,
                include_content=True
            )
            
            if not source_page or not source_page.page:
                raise Exception(f"Source page '{from_path}' not found")
            
            source_content = source_page.page.content or ""
            
            # Step 2: Create the page at the target location
            try:
                target_page = self.create_wiki_page(
                    project=project,
                    wiki_identifier=wiki_identifier,
                    path=to_path,
                    content=source_content
                )
            except Exception as create_error:
                raise Exception(f"Failed to create page at target location '{to_path}': {str(create_error)}")
            
            # Step 3: Delete the original page (only if creation succeeded)
            try:
                self.delete_wiki_page(
                    project=project,
                    wiki_identifier=wiki_identifier,
                    path=from_path
                )
            except Exception as delete_error:
                # If deletion fails, we should warn but not fail the whole operation
                # since the content is now at the target location
                return {
                    "status": "partial_success",
                    "message": f"Page moved to '{to_path}' but failed to delete original at '{from_path}': {str(delete_error)}",
                    "from_path": from_path,
                    "to_path": to_path,
                    "target_page": {
                        "path": target_page.page.path,
                        "url": target_page.page.url
                    },
                    "warning": f"Original page at '{from_path}' still exists and may need manual deletion"
                }
            
            # Success - both operations completed
            return {
                "status": "success",
                "message": f"Page successfully moved from '{from_path}' to '{to_path}'",
                "from_path": from_path,
                "to_path": to_path,
                "target_page": {
                    "path": target_page.page.path,
                    "url": target_page.page.url
                }
            }
            
        except Exception as e:
            # Complete failure - operation couldn't proceed
            raise Exception(f"Failed to move wiki page from '{from_path}' to '{to_path}': {str(e)}")

    def list_wiki_pages(self, project, wiki_identifier):
        pages_batch_request = WikiPagesBatchRequest(
            top=100  # Retrieve up to 100 pages
        )
        pages = self.wiki_client.get_pages_batch(
            project=project,
            wiki_identifier=wiki_identifier,
            pages_batch_request=pages_batch_request
        )
        return [
            {
                "path": page.path,
                "url": getattr(page, 'url', ''),  # Handle missing url attribute
                "view_stats": [
                    {"date": stat.date.isoformat(), "count": stat.count}
                    for stat in page.view_stats
                ] if page.view_stats else []
            }
            for page in pages
        ]

    def get_wikis(self, project):
        return self.wiki_client.get_all_wikis(project=project)

    def create_wiki(self, project, name):
        project_object = self.core_client.get_project(project)
        wiki_params = WikiCreateParametersV2(name=name, type='projectWiki', project_id=project_object.id)
        return self.wiki_client.create_wiki(wiki_create_params=wiki_params, project=project)

    def list_repositories(self, project):
        return self.git_client.get_repositories(project=project)

    def list_files(self, project, repository_id, path):
        return self.git_client.get_items(
            project=project,
            repository_id=repository_id,
            scope_path=path,
            recursion_level='full'
        )

    def get_file_content(self, project, repository_id, path):
        return self.git_client.get_item_text(
            project=project,
            repository_id=repository_id,
            path=path
        )

    def get_work_item_types(self, project):
        """
        Get all work item types available in a project.
        """
        return self.work_item_tracking_client.get_work_item_types(project=project)

    def get_work_item_states(self, project, work_item_type):
        """
        Get all possible states for a specific work item type.
        """
        work_item_type_obj = self.work_item_tracking_client.get_work_item_type(
            project=project,
            type=work_item_type
        )
        
        # Extract states from the work item type definition
        states = []
        if hasattr(work_item_type_obj, 'states') and work_item_type_obj.states:
            states = [
                {
                    "name": state.name,
                    "color": getattr(state, 'color', None),
                    "category": getattr(state, 'category', None)
                }
                for state in work_item_type_obj.states
            ]
        
        return states

    def get_work_item_fields(self, project):
        """
        Get all work item fields available in a project.
        """
        fields = self.work_item_tracking_client.get_fields(project=project)
        return [
            {
                "name": field.name,
                "reference_name": field.reference_name,
                "type": getattr(field, 'type', None),
                "description": getattr(field, 'description', None),
                "read_only": getattr(field, 'read_only', False),
                "can_sort_by": getattr(field, 'can_sort_by', False)
            }
            for field in fields
        ]

    def get_work_item_transitions(self, project, work_item_type, from_state):
        """
        Get valid state transitions for a work item type from a specific state.
        """
        try:
            # This requires calling the process configuration API
            # which might not be directly available in the Python SDK
            # We'll use the work item type to get transition info
            work_item_type_obj = self.work_item_tracking_client.get_work_item_type(
                project=project,
                type=work_item_type
            )
            
            # Extract transition rules if available
            transitions = []
            if hasattr(work_item_type_obj, 'transitions') and work_item_type_obj.transitions:
                transitions = [
                    {
                        "to": getattr(transition, 'to', None),
                        "actions": getattr(transition, 'actions', [])
                    }
                    for transition in work_item_type_obj.transitions
                    if hasattr(transition, 'from') and getattr(transition, 'from', None) == from_state
                ]
            else:
                # Fallback: return all available states as potential transitions
                if hasattr(work_item_type_obj, 'states') and work_item_type_obj.states:
                    transitions = [
                        {
                            "to": state.name,
                            "actions": []
                        }
                        for state in work_item_type_obj.states
                        if state.name != from_state
                    ]
            
            return transitions
        except Exception as e:
            # Fallback: return empty transitions with error info
            return {"error": str(e), "transitions": []}

    def list_iterations(self, project=None, team=None):
        """
        List all iterations in a project with their dates and time frame status.
        
        Args:
            project (str, optional): Project name or ID. If not provided, uses project_context
            team (str, optional): Team name. If not provided, uses project's default team
            
        Returns:
            list: List of iterations with id, name, path, start_date, finish_date, time_frame, url
        """
        # Use provided project or fallback to context
        project_name = project or self.project_context
        if not project_name:
            raise ValueError(
                "Project must be specified either as parameter or set via set_project_context tool. "
                "Use set_project_context to set the project context for subsequent commands."
            )
        
        # Get team context - if team not provided, get project's default team
        if not team:
            # Get the project to find its default team
            project_obj = self.core_client.get_project(project_name)
            # Use the default team name from the project
            team = project_obj.default_team.name if hasattr(project_obj, 'default_team') and project_obj.default_team else project_name
        
        # Create team context object for the API call
        from azure.devops.v7_1.work.models import TeamContext
        team_context = TeamContext(project=project_name, team=team)
        
        # Get iterations from work client
        iterations = self.work_client.get_team_iterations(team_context=team_context)
        
        # Format the response
        result = []
        for iteration in iterations:
            iteration_data = {
                "id": iteration.id if hasattr(iteration, 'id') else None,
                "name": iteration.name if hasattr(iteration, 'name') else None,
                "path": iteration.path if hasattr(iteration, 'path') else None,
                "start_date": iteration.attributes.start_date.isoformat() if hasattr(iteration, 'attributes') and iteration.attributes and hasattr(iteration.attributes, 'start_date') and iteration.attributes.start_date else None,
                "finish_date": iteration.attributes.finish_date.isoformat() if hasattr(iteration, 'attributes') and iteration.attributes and hasattr(iteration.attributes, 'finish_date') and iteration.attributes.finish_date else None,
                "time_frame": iteration.attributes.time_frame if hasattr(iteration, 'attributes') and iteration.attributes and hasattr(iteration.attributes, 'time_frame') else None,
                "url": iteration.url if hasattr(iteration, 'url') else None
            }
            result.append(iteration_data)
        
        # Sort by start_date ascending
        result.sort(key=lambda x: x['start_date'] if x['start_date'] else '1900-01-01')
        
        return result

    def get_current_iteration(self, project=None, team=None):
        """
        Get the currently active iteration based on today's date.
        
        Args:
            project (str, optional): Project name or ID. If not provided, uses project_context
            team (str, optional): Team name. If not provided, uses project's default team
            
        Returns:
            dict: Current iteration with id, name, path, start_date, finish_date, time_frame, url
        """
        # Get all iterations
        iterations = self.list_iterations(project=project, team=team)
        
        # Find the current iteration (time_frame == "current")
        current_iterations = [it for it in iterations if it.get('time_frame') == 'current']
        
        if not current_iterations:
            raise ValueError("No current iteration found. The project may not have an active iteration.")
        
        # Return the first current iteration (should only be one)
        return current_iterations[0]

    def list_iteration_work_items(self, iteration_path, project=None, team=None):
        """
        List all work items assigned to a specific iteration.
        
        Args:
            iteration_path (str): Full iteration path (e.g., "ProjectName\\Sprint 1")
            project (str, optional): Project name or ID. If not provided, uses project_context
            team (str, optional): Team name. If not provided, uses project's default team
            
        Returns:
            list: List of work items with id, title, work_item_type, state, assigned_to, iteration_path, url
        """
        # Use provided project or fallback to context
        project_name = project or self.project_context
        if not project_name:
            raise ValueError(
                "Project must be specified either as parameter or set via set_project_context tool. "
                "Use set_project_context to set the project context for subsequent commands."
            )
        
        # Build WIQL query to get all work items in the iteration
        wiql_query = f"""
        SELECT [System.Id]
        FROM WorkItems
        WHERE [System.TeamProject] = '{project_name}'
        AND [System.IterationPath] = '{iteration_path}'
        ORDER BY [System.Id]
        """
        
        wiql = Wiql(query=wiql_query)
        query_result = self.work_item_tracking_client.query_by_wiql(wiql)
        
        if not query_result.work_items:
            return []
        
        # Get full work item details
        work_item_ids = [item.id for item in query_result.work_items]
        work_items = self.work_item_tracking_client.get_work_items(ids=work_item_ids)
        
        # Format the response
        result = []
        for wi in work_items:
            work_item_data = {
                "id": wi.id,
                "title": wi.fields.get("System.Title"),
                "work_item_type": wi.fields.get("System.WorkItemType"),
                "state": wi.fields.get("System.State"),
                "assigned_to": wi.fields.get("System.AssignedTo", {}).get("displayName") if isinstance(wi.fields.get("System.AssignedTo"), dict) else wi.fields.get("System.AssignedTo"),
                "iteration_path": wi.fields.get("System.IterationPath"),
                "url": wi.url
            }
            result.append(work_item_data)
        
        return result
