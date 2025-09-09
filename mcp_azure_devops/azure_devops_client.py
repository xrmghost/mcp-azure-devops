import os
from msrest.authentication import BasicAuthentication
from azure.devops.connection import Connection
from azure.devops.v7_1.work_item_tracking.models import JsonPatchOperation, Wiql
from azure.devops.v7_1.wiki.models import WikiCreateParametersV2, WikiPagesBatchRequest
from azure.devops.v7_1.graph.graph_client import GraphClient

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

    def create_work_item(self, project, work_item_type, title, description, relations=None):
        patch_document = [
            JsonPatchOperation(
                op="add",
                path="/fields/System.Title",
                value=title
            ),
            JsonPatchOperation(
                op="add",
                path="/fields/System.Description",
                value=description
            )
        ]

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
        return result

    def update_work_item(self, work_item_id, updates, relations=None):
        patch_document = [
            JsonPatchOperation(
                op="add",
                path=f"/fields/{field}",
                value=value
            ) for field, value in updates.items()
        ]

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
