from textual import on
from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Label,
    OptionList,
    Static
)
from textual.widgets.option_list import Option

class SelectCollectionScreen(ModalScreen):
    """Screen to select an existing collection."""

    DEFAULT_CSS = """
    SelectCollectionScreen {
        align: center middle;
    }

    #dialog {
        padding: 1 1;
        width: 50%;
        height: auto;
        border: thick $background 50%;
        background: $surface 90%;
    }

    #select_label {
        height: 1;
        padding-left: 1;
        padding-right: 1;
        margin-bottom: 1;
        content-align: left middle;
    }

    OptionList {
        margin-bottom: 1;
    }

    #use_selected {
        width: 100%;
        margin-left: 1;
        margin-right: 1;
        margin-bottom: 1;
        box-sizing: border-box;
        content-align: center middle;
    }
    #use_selected:focus {
        text-style: bold;
    }

    #add_new_collection {
        width: 100%;
        margin-left: 1;
        margin-right: 1;
        box-sizing: border-box;
        content-align: center middle;
    }
    #add_new_collection:focus {
        text-style: bold;
    }

    .error {
        color: red;
        margin-top: 1;
        content-align: center middle;
    }
    """

    def __init__(self) -> None:
        super().__init__()
        self.options = [Option(name, id=f"{name}") for name in self.app.collection_names]

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Select a Collection", id="select_label"),
            OptionList(*self.options, id="collection_option_list"),
            Button("Use Selected", variant="success", id="use_selected"),
            Button("Add a New Collection", variant="primary", id="add_new_collection"),
            id="dialog",
        )

    @on(Button.Pressed, "#use_selected")
    async def action_use_selected(self) -> None:
        option_list = self.query_one("#collection_option_list", OptionList)
        selected_option = option_list.highlighted

        if selected_option is not None:
            collection_name = option_list.get_option_at_index(selected_option).id
            self.dismiss(collection_name)
        else:
            container = self.query_one("#dialog", Vertical)
            container.mount(Static("No collection selected.", classes="message"))

    @on(Button.Pressed, "#add_new_collection")
    async def action_add_new(self) -> None:
        def add_collection(collection_name: str | None) -> None:
            if collection_name:
                # Associate file with collection
                self.dismiss(collection_name)

        # Transition to the screen for adding a new collection
        self.app.push_screen("add_collection", add_collection)

    async def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        try:
            message = self.query_one(".message", Static)
            message.remove()
        except:
            pass
