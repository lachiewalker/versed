from textual.app import ComposeResult
from textual.containers import Container, Horizontal
from textual.screen import Screen
from textual.widgets import (
    Footer,
    Header
)

from panes.chat_pane import ChatPane
from panes.directory_pane import DirectoryPane


class Canvas(Container):
    """A container with a 40/60 horizontal split."""

    def __init__(self, app_name):
        super().__init__()
        self.app_name = app_name

    def compose(self) -> ComposeResult:
        with Horizontal(id="horizontal-split"):
            self.dir_pane = DirectoryPane()
            self.chat_pane =  ChatPane(self.app_name)
            yield self.dir_pane
            yield self.chat_pane


class ChatScreen(Screen):
    """Main screen containing the layout."""

    DEFAULT_CSS = """
    Canvas {
        width: 100%;
        height: 100%;
    }

    Footer {
        dock: bottom;
    }
    """

    def __init__(self, app_name):
        super().__init__()
        self.app_name = app_name    

    def compose(self) -> ComposeResult:
        yield Header()
        yield Canvas(self.app_name)
        yield Footer()