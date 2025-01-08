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

from versed.secret_handler import SecretHandler
import asyncio
from openai import OpenAI


class AddKeyScreen(ModalScreen):
    """Screen with a dialog to quit."""

    DEFAULT_CSS = """
    AddKeyScreen {
        align: center middle;
    }

    #dialog {
        padding: 1 1;
        width: 50%;
        height: auto;
        border: thick $background 50%;
        background: $surface 90%;
    }

    #alias_label, #key_label {
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

    .error {
        color: red;
        margin-top: 1;
        content-align: center middle;
    }
    """

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Key Alias", id="alias_label"),
            Input(
                placeholder="Key alias",
                restrict=r"[a-zA-Z0-9_-]*",
                max_length=24,
                id="alias_input"
            ),
            Label("OpenAI API Key", id="key_label"),
            Input(placeholder="API key", id="key_input"),
            Button("Submit", variant="success", id="submit"),
            Button("Back to Key Select", variant="primary", id="back"),
            id="dialog",
        )

    async def validate_api_key(self, api_key: str) -> bool:
        """Validate the OpenAI API key by attempting to list models."""
        try:
            client = OpenAI(api_key=api_key)
            models = client.models.list()  # Perform the call in a thread
            return True
        except:
            return False

    async def show_message(self, message: str, css_classes: str) -> None:
        """Display a temporary message at the bottom of the dialog."""
        try:
            indicator = self.query_one(".error", Static)
            await indicator.remove()
        except:
            pass

        message_label = Static(message, classes=css_classes)
        dialog = self.query_one("#dialog", Vertical)
        dialog.mount(message_label)

    @on(Button.Pressed, "#submit")
    async def action_submit(self) -> None:
        alias = self.query_one("#alias_input", Input).value
        api_key = self.query_one("#key_input", Input).value

        async def handle_submit() -> None:
            if await self.validate_api_key(api_key):
                submit_button = self.query_one("#submit", Button)
                back_button = self.query_one("#back", Button)
                alias_input = self.query_one("#alias_input", Input)
                key_input = self.query_one("#key_input", Input)

                await self.show_message("Success!", "success")

                # Store the encrypted api key
                secret_handler = SecretHandler(self.app.app_name)
                secret_handler.save_api_key(api_key, alias)

                # Disable clickables
                submit_button.disabled = True
                back_button.disabled = True
                alias_input.disabled = True
                key_input.disabled = True

                await asyncio.sleep(2)

                # Load into main chat screen
                self.app.pop_screen()
                self.app.push_screen("chat")
            else:
                await self.show_message("API key invalid.", "error")
                indicator = self.query_one("#key_input", Input)
                indicator.value = ""

        asyncio.create_task(handle_submit())
    
    @on(Button.Pressed, "#back")
    async def action_back(self) -> None:
        self.app.pop_screen()
        self.app.push_screen("load_key")
