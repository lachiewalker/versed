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

class LoadProjectScreen(ModalScreen):
    """Screen to select a saved API key."""

    DEFAULT_CSS = """
    LoadProjectScreen {
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

    #add_new_project {
        width: 100%;
        margin-left: 1;
        margin-right: 1;
        box-sizing: border-box;
        content-align: center middle;
    }
    #add_new_project:focus {
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
        self.options = [Option(alias, id=f"{alias}") for alias in self.aliases]

    def compose(self) -> ComposeResult:
        yield Vertical(
            Label("Select a Project", id="select_label"),
            OptionList(*self.options, id="project_option_list"),
            Button("Use Selected", variant="success", id="use_selected"),
            Button("Add a New Project", variant="primary", id="add_new_project"),
            id="dialog",
        )

    @on(Button.Pressed, "#use_selected")
    async def action_use_selected(self) -> None:
        option_list = self.query_one("#project_option_list", OptionList)
        selected_option = option_list.highlighted

        if selected_option is not None:
            project = option_list.get_option_at_index(selected_option).id
            self.dismiss(project)
        else:
            container = self.query_one("#dialog", Vertical)
            container.mount(Static("No project selected.", classes="message"))

    @on(Button.Pressed, "#add_new_project")
    async def action_add_new(self) -> None:
        def add_project(project_name: str | None) -> None:
            if project_name:
                self.dismiss(project_name)

        # Transition to the screen for adding a new API key
        self.app.push_screen("add_project", add_project)

    async def on_option_list_option_selected(
        self, event: OptionList.OptionSelected
    ) -> None:
        try:
            message = self.query_one(".message", Static)
            message.remove()
        except:
            pass
