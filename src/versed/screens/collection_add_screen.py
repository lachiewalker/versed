from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Input,
    Label,
    Static
)


class AddCollectionScreen(ModalScreen):
    """Screen to add a new collection."""

    DEFAULT_CSS = """
    AddCollectionScreen {
        align: center middle;
    }

    #dialog {
        padding: 1 1;
        width: 50%;
        height: auto;
        border: thick $background 50%;
        background: $surface 90%;
    }

    #name_label {
        height: 1;
        padding-left: 1;
        padding-right: 1;
        content-align: left middle;
    }

    Input {
        height: 1fr;
        margin-bottom: 1;
        content-align: left middle;
    }

    #submit {
        width: 100%;
        margin-left: 1;
        margin-right: 1;
        margin-bottom: 1;
        box-sizing: border-box;
        content-align: center middle;
    }
    #submit:focus {
        text-style: bold;
    }

    #back {
        width: 100%;
        margin-left: 1;
        margin-right: 1;
        box-sizing: border-box;
        content-align: center middle;
    }
    #back:focus {
        text-style: bold;
    }

    .success {
        color: green;
        margin-top: 1;
        content-align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Collection Name", id="name_label"),
            Input(
                placeholder="Collection name",
                restrict=r"[a-zA-Z0-9_]*",
                max_length=64,
                id="name_input"
            ),
            Button("Submit", variant="success", id="submit"),
            Button("Back to Collection Select", variant="primary", id="back"),
            id="dialog",
        )

    async def show_message(self, message: str, css_classes: str) -> None:
        """Display a temporary message at the bottom of the dialog."""
        message_label = Static(message, classes=css_classes)
        dialog = self.query_one("#dialog", Vertical)
        dialog.mount(message_label)

    @on(Button.Pressed, "#submit")
    async def action_submit(self) -> None:
        collection_name = self.query_one("#name_input", Input).value

        submit_button = self.query_one("#submit", Button)
        back_button = self.query_one("#back", Button)
        name_input = self.query_one("#name_input", Input)

        self.app.vector_store.add_collection(collection_name, callback=self.app.on_vector_store_update)

        chat_screen = self.app.get_screen("chat")
        if chat_screen is not None:
            collection_selector = chat_screen.query_one("#collection-selector")
        collection_selector.add_option(
            (collection_name, collection_name, True)
        )
        await self.show_message("Collection Added", "success")

        # Disable clickables
        submit_button.disabled = True
        back_button.disabled = True
        name_input.disabled = True

        self.dismiss(collection_name)
    
    @on(Button.Pressed, "#back")
    async def action_back(self) -> None:
        self.dismiss(None)