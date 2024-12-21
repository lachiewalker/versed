from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import (
    Header,
    Footer
)
from textual.screen import Screen
from textual.events import Resize

from panes.directory_pane import DirectoryPane
from panes.chat_pane import ChatPane


class Canvas(Container):
    """A container with a 40/60 horizontal split."""

    def compose(self) -> ComposeResult:
        with Horizontal(id="horizontal-split"):
            self.dir_pane = DirectoryPane()
            self.chat_pane =  ChatPane()
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
    

    def compose(self) -> ComposeResult:
        yield Header()
        yield Canvas()
        yield Footer()


class DocumentChat(App):
    """Main app that pushes the ChatScreen on startup."""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]

    def on_ready(self) -> None:
        self.push_screen(ChatScreen())

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    app = DocumentChat()
    app.run()

