from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import (
    DirectoryTree,
    TabPane,
    TabbedContent,
    Tree
)
from textual.widgets.tree import TreeNode

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class GoogleDriveTree(Tree):

    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

    def __init__(self, label, id="google-drive-tree"):
        super().__init__(label, id=id)

        credentials = self.app.credentials
        service = build('drive', 'v3', credentials=credentials)

        # Fetch Google Drive files and build the tree
        google_drive_structure = self.fetch_google_drive_files(service)
        self.build_tree(self.root, google_drive_structure)

    def build_tree(self, parent: TreeNode, drive_tree: dict):
        """
        Build the hierarchy of files and folders used to populate the tree.
        """
        folders = []
        files = []

        for name, children in drive_tree.items():
            if children:
                folders.append((name, children))
            else:
                files.append(name)

        # Sort folders and files alphabetically
        folders.sort(key=lambda x: x[0].lower())
        files.sort(key=lambda x: x.lower())

        # Add folders to the tree first
        for name, children in folders:
            node = parent.add(f"📁 {name}", expand=False)
            node.data = {"name": name, "type": "folder"}
            self.build_tree(node, children)

        # Add files to the tree after folders
        for name in files:
            parent.add(f"📄 {name}", data={"name": name, "type": "file"})

    def authenticate_with_browser(self):
        """
        Authenticate the user using OAuth 2.0 and return credentials.
        """
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', self.SCOPES
        )
        # Run local server for OAuth 2.0 redirect
        creds = flow.run_local_server(port=8080)
        return creds

    def fetch_google_drive_files(self, service, folder_id="root"):
        """
        Recursively fetch Google Drive files and folders.
        """
        results = service.files().list(
            q=f"'{folder_id}' in parents and trashed = false",
            fields="files(id, name, mimeType, parents)"
        ).execute()

        files = results.get('files', [])
        tree = {}
        for file in files:
            if file["mimeType"] == "application/vnd.google-apps.folder":
                tree[file["name"]] = self.fetch_google_drive_files(service, file["id"])
            else:
                tree[file["name"]] = None
        return tree
    
    async def on_tree_node_expanded(self, event: Tree.NodeExpanded) -> None:
        """Update the folder icon when a folder is expanded."""
        node = event.node
        if node.data and node.data.get("type") == "folder":
            node.set_label(f"📂 {node.label[2:]}")

    async def on_tree_node_collapsed(self, event: Tree.NodeCollapsed) -> None:
        """Update the folder icon when a folder is collapsed."""
        node = event.node
        if node.data and node.data.get("type") == "folder":
            node.set_label(f"📁 {node.label[2:]}")


class DirectoryPane(Container):
    """Tabbed pane containing DirectoryTrees for file sources and destination index."""
    
    DEFAULT_CSS = """
    DirectoryPane {
        width: 42;
    }

    TabPane {
        background: $background-lighten-1;
        padding: 1;
    }

    DirectoryTree {
        height: 1fr;
    }
    """

    def compose(self) -> ComposeResult:
        with TabbedContent():
            with TabPane("Indexed Files", id="indexed-files"):
                yield DirectoryTree(".", id="index-tree")
            with TabPane("Local Files", id="local-files"):
                yield DirectoryTree(".", id="local-tree")
            with TabPane("Google Drive", id="google-drive"):
                yield GoogleDriveTree("Google Drive", id="gdrive-tree")
