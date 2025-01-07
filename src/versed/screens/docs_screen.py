import json
from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Static

class DocsScreen(ModalScreen):

    DEFAULT_CSS = """
    DocsScreen {
        align: center middle;
    }

    #dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 3;
        padding: 0 1;
        width: 60;
        height: 11;
        border: thick $background 50%;
        background: $surface 90%;
    }

    #back {
        dock: bottom;
        width: 100%;
        margin-left: 3;
        margin-right: 3;
        box-sizing: border-box;
        content-align: center middle;
    }
    #back:focus {
        text-style: bold;
    }
    """

    def compose(self) -> ComposeResult:
        # Display each document on a new line.
        stats = self.app.stats
        content = json.dumps(stats) if stats else "No documents found."
        yield Vertical(
            Static(content),
            Button("Close", variant="primary", id="back"),
            id="dialog"
        )

    @on(Button.Pressed, "#back")
    async def action_back(self) -> None:
        self.app.pop_screen()
