from textual.app import ComposeResult
from textual.containers import Container
from textual.widgets import (
    TabPane,
    TabbedContent,
    DirectoryTree,
)


class DirectoryPane(Container):
    """Tabbed pane containing DirectoryTrees for file sources and destination index."""\
    
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
                yield DirectoryTree(".", id="gdrive-tree")
