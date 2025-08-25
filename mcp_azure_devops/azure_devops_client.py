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
        self._initialized = False
        self._initialization_error = None
        
        # Initialize clients as None - they'll be created on first use
        self.credentials = None
        self.connection = None
        self.core_client = None
        self.work_item_tracking_client = None
        self.wiki_client = None
        self.git_client = None
        self.graph_client = None

    def _ensure_initialized(self):
        """Ensure the client is initialized with proper credentials."""
        if self._initialized:
            return
            
        if self._initialization_error:
            raise self._initialization_error
            
        if not self.org_url or not self.pat:
            self._initialization_error = ValueError("AZURE_DEVOPS_ORG_URL and AZURE_DEVOPS_PAT environment variables must be set.")
            raise self._initialization_error
            
        try:
            self.credentials = BasicAuthentication('', self.pat)
            self.connection = Connection(base_url=self.org_url, creds=self.credentials)
            self.core_client = self.connection.clients.get_core_client()
            self.work_item_tracking_client = self.connection.clients.get_work_item_tracking_client()
            self.wiki_client = self.connection.clients.get_wiki_client()
            self.git_client = self.connection.clients.get_git_client()
            self.graph_client = self.connection.clients.get_graph_client()
            self._initialized = True
        except Exception as e:
            self._initialization_error = e
            raise

    def list_users(self):
        self._ensure_initialized()
        return self.graph_client.list_users()

    def set_project_context(self, project):
        # This doesn't require Azure DevOps connection
        self.project_context = project
        return {"message": f"Project context set to '{project}'."}

    def clear_project_context(self):
        # This doesn't require Azure DevOps connection
        self.project_context = None
        return {"message": "Project context cleared."}

    def get_projects(self):
        self._ensure_initialized()
        return self.core_client.get_projects()

    def create_work_item(self, project, work_item_type, title, description, relations=None):
        self._ensure_initialized()
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
        self._ensure_initialized()
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
        self._ensure_initialized()
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
        self._ensure_initialized()
        return self.work_item_tracking_client.delete_work_item(id=work_item_id)

    def search_work_items(self, project, wiql_query):
        self._ensure_initialized()
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
        self._ensure_initialized()
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
        self._ensure_initialized()
        return self.wiki_client.get_page(
            project=project,
            wiki_identifier=wiki_identifier,
            path=path,
            include_content=True
        )

    def update_wiki_page(self, project, wiki_identifier, path, content):
        self._ensure_initialized()
        page = self.wiki_client.get_page(
            project=project,
            wiki_identifier=wiki_identifier,
            path=path
        )
        
        parameters = {
            "content": content
        }
        return self.wiki_client.create_or_update_page(
            project=project,
            wiki_identifier=wiki_identifier,
            path=path,
            parameters=parameters,
            version=page.e_tag
        )

    def delete_wiki_page(self, project, wiki_identifier, path):
        self._ensure_initialized()
        return self.wiki_client.delete_page(
            project=project,
            wiki_identifier=wiki_identifier,
            path=path
        )

    def list_wiki_pages(self, project, wiki_identifier):
        self._ensure_initialized()
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
                "url": page.url,
                "view_stats": [
                    {"date": stat.date.isoformat(), "count": stat.count}
                    for stat in page.view_stats
                ] if page.view_stats else []
            }
            for page in pages
        ]

    def get_wikis(self, project):
        self._ensure_initialized()
        return self.wiki_client.get_all_wikis(project=project)

    def create_wiki(self, project, name):
        self._ensure_initialized()
        project_object = self.core_client.get_project(project)
        wiki_params = WikiCreateParametersV2(name=name, type='projectWiki', project_id=project_object.id)
        return self.wiki_client.create_wiki(wiki_create_params=wiki_params, project=project)

    def list_repositories(self, project):
        self._ensure_initialized()
        return self.git_client.get_repositories(project=project)

    def list_files(self, project, repository_id, path):
        self._ensure_initialized()
        return self.git_client.get_items(
            project=project,
            repository_id=repository_id,
            scope_path=path,
            recursion_level='full'
        )

    def get_file_content(self, project, repository_id, path):
        self._ensure_initialized()
        return self.git_client.get_item_text(
            project=project,
            repository_id=repository_id,
            path=path
        )
