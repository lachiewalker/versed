import asyncio
from pathlib import Path
from textual import on
from textual.app import ComposeResult
from textual.await_complete import AwaitComplete
from textual.containers import Container, Vertical
from textual.widgets import (
    Button,
    DirectoryTree,
    TabPane,
    TabbedContent,
    Tree
)
from textual.widgets.directory_tree import DirEntry
from textual.widgets.tree import TreeNode

from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build


class GoogleDriveTree(Tree):

    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

    def __init__(self, label, id="google-drive-tree"):
        super().__init__(label, id=id)

        credentials = self.app.credentials
        service = build('drive', 'v3', credentials=credentials)

        google_drive_structure = self.fetch_google_drive_files(service)
        self.build_tree(self.root, google_drive_structure)
        self.root.expand()

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
            node.data = {"name": name, "type": "folder", "path": f"gdrive://folder/{name}"}
            self.build_tree(node, children)

        for name in files:
            parent.add(f"📄 {name}", data={"name": name, "type": "file", "path": f"gdrive://file/{name}"})

    def authenticate_with_browser(self):
        """
        Authenticate the user using OAuth 2.0 and return credentials.
        """
        flow = InstalledAppFlow.from_client_secrets_file(
            'credentials.json', self.SCOPES
        )
        creds = flow.run_local_server(port=8080)    # Run local server for OAuth 2.0 redirect
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


class EmptyDirectoryTree(DirectoryTree):
    async def watch_path(self) -> None:
        self.clear_node(self.root)  # Prevent automatic reloading and just clear nodes.

    async def _loader(self) -> None:
        # Disable background filesystem loading.
        pass

    def _add_to_load_queue(self, node: TreeNode[DirEntry]) -> AwaitComplete:
        """
        Override to mark node as loaded without adding to the queue,
        preventing the awaitable from hanging.
        """
        if node.data and not node.data.loaded:
            node.data.loaded = True
        
        return AwaitComplete(asyncio.sleep(0))  # Return an already completed awaitable to prevent waiting.

    def __init__(
        self,
        path: str | Path = ".",
        *,
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
        disabled: bool = False,
    ) -> None:
        super().__init__(path, name=name, id=id, classes=classes, disabled=disabled)

        self.clear_node(self.root)
    

class DirectoryPane(Container):
    """Tabbed pane containing DirectoryTrees for file sources and destination index."""
    
    DEFAULT_CSS = """
    DirectoryPane {
        width: 42;
    }

    #pane-container {
        height: 1fr;
        align: center middle;
        background: $background-lighten-1;
    }

    #tabbed-content {
        height: 0.5fr;
    }

    TabPane {
        background: $background-lighten-1;
        padding: 1;
    }

    #index-button {
        width: 1fr;
        height: 3;
        margin: 1 3;
        text-align: center;
        background: $primary;
    }
    #index-button:focus {
        text-style: bold;
    }
    """

    def compose(self) -> ComposeResult:
        with Vertical(id="pane-container"):
            with TabbedContent(id="tabbed-content"):
                with TabPane("Indexed Files", id="indexed-files"):
                    yield EmptyDirectoryTree("", id="index-tree")
                with TabPane("Local Files", id="local-files"):
                    yield DirectoryTree(".", id="local-tree")
                with TabPane("Google Drive", id="google-drive"):
                    yield GoogleDriveTree("Google Drive", id="gdrive-tree")
            yield Button("Add to Index", id="index-button")

    def on_mount(self) -> None:
        # Store references to the widgets and initialize state
        self.index_tree: EmptyDirectoryTree = self.query_one("#index-tree", EmptyDirectoryTree)
        self.local_tree: DirectoryTree = self.query_one("#local-tree", DirectoryTree)
        self.gdrive_tree: DirectoryTree = self.query_one("#gdrive-tree", Tree)
        self.index_button: Button = self.query_one("#index-button", Button)

        # self.index_button.disabled = True
        self.added_files = set()
        self.selected_source = None

