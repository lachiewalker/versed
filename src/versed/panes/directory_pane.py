import asyncio
from googleapiclient.discovery import build
from pathlib import Path
from rich.style import Style
from rich.text import Text
from textual import on
from textual.app import ComposeResult
from textual.await_complete import AwaitComplete
from textual.containers import Container, Vertical
from textual.css.query import NoMatches
from textual.widgets import (
    Button,
    DirectoryTree,
    SelectionList,
    Static,
    TabPane,
    TabbedContent,
    Tree
)
from textual.widgets.directory_tree import DirEntry
from textual.widgets._tree import TOGGLE_STYLE, TreeNode
from typing import ClassVar
from versed.screens.docs_screen import DocsScreen


class GoogleDriveTree(Tree):

    SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

    ICON_NODE_EXPANDED = "📂 "
    ICON_NODE = "📁 "
    ICON_FILE = "📄 "

    COMPONENT_CLASSES: ClassVar[set[str]] = {
        "directory-tree--extension",
        "directory-tree--file",
        "directory-tree--folder",
        "directory-tree--hidden",
    }
    """
    | Class | Description |
    | :- | :- |
    | `directory-tree--extension` | Target the extension of a file name. |
    | `directory-tree--file` | Target files in the directory structure. |
    | `directory-tree--folder` | Target folders in the directory structure. |
    | `directory-tree--hidden` | Target hidden items in the directory structure. |
    """

    DEFAULT_CSS = """
    DirectoryTree {
        
        & > .directory-tree--folder {
            text-style: bold;
        }

        & > .directory-tree--extension {
            text-style: italic;
        }

        & > .directory-tree--hidden {
            color: $text 50%;
        }

        &:ansi {
        
            & > .tree--guides {
               color: transparent;              
            }
        
            & > .directory-tree--folder {
                text-style: bold;
            }

            & > .directory-tree--extension {
                text-style: italic;
            }

            & > .directory-tree--hidden {
                color: ansi_default;
                text-style: dim;
            }
        }
    }
    """


    def __init__(self, label, id="google-drive-tree"):
        super().__init__(label, id=id)

        credentials = self.app.credentials
        service = build('drive', 'v3', credentials=credentials)

        self.mimetype_extensions = self.app.mimetype_extensions

        google_drive_structure = self.fetch_google_drive_files(service)
        self.build_tree(self.root, google_drive_structure)
        self.root.expand()

    def build_tree(self, parent: TreeNode, drive_tree: dict):
        """
        Build the hierarchy of files and folders used to populate the tree.
        """
        folders = []
        files = []

        for name, data in drive_tree.items():
            if data.get("type") == "folder":
                folders.append((name, data))
            else:
                files.append((name, data))

        # Sort folders and files alphabetically
        folders.sort(key=lambda x: x[0].lower())
        files.sort(key=lambda x: x[0].lower())

        # Add folders to the tree first
        for name, data in folders:
            node = parent.add(f"{name}", expand=False)
            node.data = {
                "name": name,
                "type": "folder",
                "id": data["id"],
                "path": f"gdrive://folder/{data['id']}"
            }
            self.build_tree(node, data["children"])

        for name, data in files:
            parent.add(
                f"{name}",
                data={
                    "name": name,
                    "type": "file",
                    "id": data["id"],
                    "path": f"gdrive://file/{data['id']}"
                },
                allow_expand=False,
            )  

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
            mime_type = file["mimeType"]
            file_name = file["name"]

            # Append extension if it exists in the mapping
            extension = self._mime_to_extension(mime_type)
            if extension:
                file_name += extension

            if mime_type == "application/vnd.google-apps.folder":
                # Folder handling
                tree[file_name] = {
                    "id": file["id"],
                    "type": "folder",
                    "children": self.fetch_google_drive_files(service, file["id"]),
                }
            else:
                # File handling
                tree[file_name] = {
                    "id": file["id"],
                    "type": "file",
                }

        return tree
    
    def _mime_to_extension(self, mimetype):
        if mimetype in self.mimetype_extensions:
            return self.mimetype_extensions[mimetype]
        else:
            return None

    
    def render_label(self, node: TreeNode[DirEntry], base_style: Style, style: Style) -> Text:
        """Render a label for the given node.

        Args:
            node: A tree node.
            base_style: The base style of the widget.
            style: The additional style for the label.

        Returns:
            A Rich Text object containing the label.
        """
        node_label = node._label.copy()
        node_label.stylize(style)

        # If the tree isn't mounted yet we can't use component classes to stylize
        # the label fully, so we return early.
        if not self.is_mounted:
            return node_label

        if node._allow_expand:
            prefix = (
                self.ICON_NODE_EXPANDED if node.is_expanded else self.ICON_NODE,
                base_style + TOGGLE_STYLE,
            )
            node_label.stylize_before(
                self.get_component_rich_style("directory-tree--folder", partial=True)
            )
        else:
            prefix = (
                self.ICON_FILE,
                base_style,
            )
            node_label.stylize_before(
                self.get_component_rich_style("directory-tree--file", partial=True),
            )
            node_label.highlight_regex(
                r"\..+$",
                self.get_component_rich_style(
                    "directory-tree--extension", partial=True
                ),
            )

        if node_label.plain.startswith("."):
            node_label.stylize_before(
                self.get_component_rich_style("directory-tree--hidden")
            )

        text = Text.assemble(prefix, node_label)
        return text


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

    BINDINGS = [
        ("v", "view_docs", "View Documents")
    ]
    
    DEFAULT_CSS = """
    DirectoryPane {
        width: 42;

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

        #remove-button {
            width: 1fr;
            height: 3;
            margin: 1 3;
            text-align: center;
            background: $error;
        }
        #remove-button:focus {
            text-style: bold;
        }
    }
    """
    def __init__(self) -> None:
        super().__init__()
        self.logged_in = False
        self.selected_node = None
        self.highlighted_collection = None

    def compose(self) -> ComposeResult:
        with Vertical(id="pane-container"):
            with TabbedContent(id="tabbed-content"):
                with TabPane("Collections", id="collections-tab"):
                    collection_names = self.app.collection_names
                    selections = [(name, name, False) for name in collection_names]
                    yield SelectionList[str](  
                        *selections,
                        id="collection-selector"
                    )
                with TabPane("Local Files", id="local-files"):
                    yield DirectoryTree(".", id="local-tree")
                with TabPane("Google Drive", id="google-drive"):
                    self.log_in = Button("Log in", variant="success", id="log-in")
                    yield self.log_in
            yield Button("Add to Index", id="index-button")
            yield Button("Remove Collection", id="remove-button")

    def on_mount(self) -> None:
        self.index_tab = self.query_one("#collections-tab", TabPane)
        self.local_tab = self.query_one("#local-files", TabPane)
        self.gdrive_tab = self.query_one("#google-drive", TabPane)
        self.index_button = self.query_one("#index-button", Button)

        self.index_button.disabled = True
        self.added_files = set()

    def node_is_dir(self, node) -> bool:
        return True if node._allow_expand else False
    
    def get_node_path(self, node) -> str:
        """
        Retrieve the path from a TreeNode, whether from a DirectoryTree or GoogleDriveTree.

        Args:
            node (TreeNode): A node from either DirectoryTree or GoogleDriveTree.

        Returns:
            str: The path of the node as a string, or None if no path exists.
        """
        if node and node.data:
            if hasattr(node.data, "path"):  # Handle DirectoryTree (node.data is a DirEntry)
                return str(node.data.path)
            
            elif isinstance(node.data, dict) and "path" in node.data:
                return node.data["path"]
        
        return None
    
    def get_node_name(self, node) -> str:
        """
        Retrieve the path from a TreeNode, whether from a DirectoryTree or GoogleDriveTree.

        Args:
            node (TreeNode): A node from either DirectoryTree or GoogleDriveTree.

        Returns:
            str: The path of the node as a string, or None if no path exists.
        """
        if node and node.data:
            if hasattr(node.data, "path"):  # Handle DirectoryTree (node.data is a DirEntry)
                return str(node.data.path.name)
            
            elif isinstance(node.data, dict) and "path" in node.data:
                return node.data["name"]
        
        return None

    def add_to_collection(self, collection, node):
        # self.app.push_screen(DebugScreen(collection + " || " + str(type(collection))))
        if self.node_is_dir(node):
            pass
        else:
            path = self.get_node_path(node)
            file_name = self.get_node_name(node)
            file = {
                "name": file_name,
                "path": path
            }
            self.app.vector_store.add_files_to_collection(collection=collection, files=[file])

    @on(Button.Pressed, "#log-in")
    async def action_log_in(self) -> None:
        google_tab = self.query_one("#google-drive", TabPane)
        login_button = self.query_one("#log-in", Button)
        if self.app.credentials:
            login_button.remove()
            google_tab.mount(GoogleDriveTree("Google Drive", id="gdrive-tree"))
        else:
            try:
                self.app.auth_handler.get_credentials()
                login_button.remove()
                google_tab.mount(GoogleDriveTree("Google Drive", id="gdrive-tree"))
                self.logged_in = True
            except FileNotFoundError:
                google_tab.mount(Static("Credentials file not found."))
                login_button.disabled = True

    @on(Button.Pressed, "#index-button")
    async def action_index(self) -> None:
        def select_collection(collection_name: str | None) -> None:
            if collection_name:
                self.add_to_collection(collection=collection_name, node=self.selected_node)

        # Transition to the add collection screen
        self.app.push_screen("select_collection", select_collection)

    @on(Button.Pressed, "#remove-button")
    async def action_remove(self) -> None:
        if self.highlighted_collection is not None:
            self.app.vector_store.remove_collection(self.highlighted_collection, callback=self.app.on_vector_store_update)

    @on(DirectoryTree.FileSelected, "#local-tree")
    async def action_handle_local_file_selection(self, event: DirectoryTree.NodeSelected) -> None:
        """Enable the button when a node is selected in the DirectoryTree."""
        self.query_one("#index-button", Button).disabled = False
        self.selected_node = event.node

    @on(DirectoryTree.DirectorySelected, "#local-tree")
    async def action_handle_local_dir_selection(self, event: DirectoryTree.NodeSelected) -> None:
        """Enable the button when a node is selected in the DirectoryTree."""
        self.query_one("#index-button", Button).disabled = False
        self.selected_node = event.node

    @on(GoogleDriveTree.NodeSelected, "#gdrive-tree")
    async def action_handle_google_selection(self, event: DirectoryTree.NodeSelected) -> None:
        """Enable the button when a node is selected in the DirectoryTree."""
        self.query_one("#index-button", Button).disabled = False
        self.selected_node = event.node
        # is_dir = self.node_is_dir(event.node)

    @on(SelectionList.SelectionHighlighted, "#collection-selector")
    async def action_collection_highlighted(self, event) -> None:
        highlighted_selection = event.selection
        if highlighted_selection is not None:
            self.highlighted_collection = str(highlighted_selection.prompt)
    
    @on(TabbedContent.TabActivated)
    async def reset_button_on_tab_show(self, event: TabbedContent.TabActivated) -> None:
        """Disable the button when the Local Files tab is shown."""
        add_to_index_button = self.query_one("#index-button", Button)
        remove_collection_button = self.query_one("#remove-button", Button)

        # Handle button visibility
        if event.pane.id == "collections-tab":
            add_to_index_button.display = "none"
            remove_collection_button.display = "block"
        else:
            add_to_index_button.display = "block"
            remove_collection_button.display = "none"

        # Handle index button enablement
        tab_pane = event.pane
        if tab_pane.id in ["local-files", "google-drive"]:
            add_to_index_button.disabled = True
            try:
                tree = tab_pane.query_one(Tree)
                tree.move_cursor(None)
            except NoMatches:
                pass

    async def action_view_docs(self) -> None:
        """
        Fetches stats about the vector collection and displays them in a modal screen.
        """
        collections_selector = self.query_one("#collection-selector")
        selected_index = collections_selector.highlighted
        if selected_index is not None:
            selected_option = collections_selector.get_option_at_index(selected_index)
            selected_collection = selected_option.value
        
        # Push the modal screen with retrieved documents
        await self.app.push_screen(DocsScreen(selected_collection))
