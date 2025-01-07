import asyncio
from pathlib import Path
from textual import on
from textual.app import ComposeResult
from textual.await_complete import AwaitComplete
from textual.containers import Container, Vertical
from textual.widgets import (
    Button,
    DirectoryTree,
    Static,
    TabPane,
    TabbedContent,
    Tree
)
from textual.widgets.directory_tree import DirEntry
from textual.widgets.tree import TreeNode

from googleapiclient.discovery import build


class GoogleDriveTree(DirectoryTree):

    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

    def __init__(self, label, id="google-drive-tree"):
        super().__init__(label, id=id)

        credentials = self.app.credentials
        service = build('drive', 'v3', credentials=credentials)

        asyncio.create_task(self.load_google_drive_files(service))

    async def load_google_drive_files(self, service):
        drive_structure = await self.fetch_google_drive_files(service)
        self.build_tree(self.root, drive_structure)
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
            node.data = {"name": name, "type": "folder", "path": f"gdrive://folder/{name}", "loaded": False}
            self.build_tree(node, children)

        for name in files:
            parent.add(f"📄 {name}", data={"name": name, "type": "file", "path": f"gdrive://file/{name}", "loaded": True})

    async def fetch_google_drive_files(self, service, folder_id="root"):
        """
        Recursively fetch Google Drive files and folders.
        """
        # results = service.files().list(
        #     q=f"'{folder_id}' in parents and trashed = false",
        #     fields="files(id, name, mimeType, parents)"
        # ).execute()
        results = await asyncio.to_thread(service.files().list,
                                          q=f"'{folder_id}' in parents and trashed = false",
                                          fields="files(id, name, mimeType, parents)").execute

        files = results.get('files', [])
        tree = {}
        for file in files:
            if file["mimeType"] == "application/vnd.google-apps.folder":
                tree[file["name"]] = self.fetch_google_drive_files(service, file["id"])
            else:
                tree[file["name"]] = None
        return tree
    
    async def watch_path(self):
        self.clear_node(self.root)

    async def _loader(self):
        pass

    def _add_to_load_queue(self, node: TreeNode):
        if node.data and not node.data.get('loaded', False):
            node.data['loaded'] = True
        return asyncio.sleep(0)  # Return an already completed awaitable


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

    #google-drive {
        height: 1fr;
        align: center middle;
    }

    #log-in {
        width: 8;
        height: 3;
        text-align: center;
    }
    #log-in:focus {
        text-style: bold;
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
                    self.log_in = Button("Log in", variant="success", id="log-in")
                    yield self.log_in
            yield Button("Add to Index", id="index-button")

    def on_mount(self) -> None:
        # Store references to the widgets and initialize state
        self.indexed_tab = self.query_one("#indexed-files", TabPane)
        self.local_tab = self.query_one("#local-files", TabPane)
        self.gdrive_tab = self.query_one("#google-drive", TabPane)
        self.index_button: Button = self.query_one("#index-button", Button)

        # self.index_button.disabled = True
        self.added_files = set()
        self.selected_source = None

    @on(Button.Pressed, "#log-in")
    async def action_log_in(self) -> None:
        google_tab = self.query_one("#google-drive", TabPane)
        login_button = self.query_one("#log-in", Button)
        if self.app.credentials:
            login_button.remove()
            google_tab.mount(GoogleDriveTree("Google Drive", id="gdrive-tree"))
        else:
            google_tab.mount(Static("Credentials file not found."))
            login_button.disabled = True
