import os
from msrest.authentication import BasicAuthentication
from azure.devops.connection import Connection
from azure.devops.v7_1.work_item_tracking.models import JsonPatchOperation, Wiql

class AzureDevOpsClient:
    def __init__(self):
        self.org_url = os.getenv("AZURE_DEVOPS_ORG_URL")
        self.pat = os.getenv("AZURE_DEVOPS_PAT")
        self.project_context = None
        
        if not self.org_url or not self.pat:
            raise ValueError("AZURE_DEVOPS_ORG_URL and AZURE_DEVOPS_PAT environment variables must be set.")
            
        self.credentials = BasicAuthentication('', self.pat)
        self.connection = Connection(base_url=self.org_url, creds=self.credentials)
        self.core_client = self.connection.clients.get_core_client()
        self.work_item_tracking_client = self.connection.clients.get_work_item_tracking_client()
        self.wiki_client = self.connection.clients.get_wiki_client()
        self.git_client = self.connection.clients.get_git_client()

    def set_project_context(self, project):
        self.project_context = project
        return {"message": f"Project context set to '{project}'."}

    def clear_project_context(self):
        self.project_context = None
        return {"message": "Project context cleared."}

    def get_projects(self):
        return self.core_client.get_projects()

    def create_work_item(self, project, work_item_type, title, description):
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
        
        return self.work_item_tracking_client.create_work_item(
            document=patch_document,
            project=project,
            type=work_item_type
        )

    def get_work_item(self, work_item_id):
        work_item = self.work_item_tracking_client.get_work_item(id=work_item_id)
        return {
            "id": work_item.id,
            "url": work_item.url,
            "title": work_item.fields.get("System.Title"),
            "state": work_item.fields.get("System.State"),
            "description": work_item.fields.get("System.Description"),
        }

    def update_work_item(self, work_item_id, updates):
        patch_document = [
            JsonPatchOperation(
                op="add",
                path=f"/fields/{field}",
                value=value
            ) for field, value in updates.items()
        ]
        
        return self.work_item_tracking_client.update_work_item(
            document=patch_document,
            id=work_item_id
        )

    def delete_work_item(self, work_item_id):
        return self.work_item_tracking_client.delete_work_item(id=work_item_id)

    def search_work_items(self, project, wiql_query):
        project_object = self.core_client.get_project(project)
        project_id = project_object.id

        wiql = Wiql(query=wiql_query)
        query_result = self.work_item_tracking_client.query_by_wiql(wiql, project_id)
        
        if query_result.work_items:
            work_item_ids = [item.id for item in query_result.work_items]
            work_items = self.work_item_tracking_client.get_work_items(ids=work_item_ids, project=project_id)
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

    def delete_wiki_page(self, project, wiki_identifier, path):
        return self.wiki_client.delete_page(
            project=project,
            wiki_identifier=wiki_identifier,
            path=path
        )

    def list_wiki_pages(self, project, wiki_identifier):
        return {"message": "Listing all wiki pages is not directly supported by the current library version."}

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
