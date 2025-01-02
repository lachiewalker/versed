from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Grid
from textual.widgets import (
    Header,
    Footer,
    Label,
    Button
)
from textual.screen import Screen

from panes.directory_pane import DirectoryPane
from panes.chat_pane import ChatPane

from platformdirs import user_data_dir
from pathlib import Path
from pymilvus import MilvusClient, FieldSchema, DataType, CollectionSchema, Collection
from contextlib import contextmanager


@contextmanager
def milvus_client(uri):
    client = MilvusClient(uri=uri)
    try:
        yield client
    finally:
        client.close()


class QuitScreen(Screen):
    """Screen with a dialog to quit."""

    DEFAULT_CSS = """
    QuitScreen {
        align: center middle;
    }

    #dialog {
        grid-size: 2;
        grid-gutter: 1 2;
        grid-rows: 1fr 3;
        padding: 0 1;
        width: 60;
        height: 11;
        border: thick $background 80%;
        background: $surface;
    }

    #question {
        column-span: 2;
        height: 1fr;
        width: 1fr;
        content-align: center middle;
    }

    Button {
        width: 100%;
    }
    """

    def compose(self) -> ComposeResult:
        yield Grid(
            Label("Are you sure you want to quit?", id="question"),
            Button("Quit", variant="error", id="quit"),
            Button("Cancel", variant="primary", id="cancel"),
            id="dialog",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit()
        else:
            self.app.pop_screen()


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

    BINDINGS = [
        ("q", "request_quit", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode")
    ]

    def on_ready(self) -> None:
        self.push_screen(ChatScreen())

    def action_request_quit(self) -> None:
        self.push_screen(QuitScreen())

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    app_name = "versed"
    data_dir = Path(user_data_dir(app_name))
    data_dir.mkdir(parents=True, exist_ok=True)

    # Define the path for the Milvus database file
    milvus_db_path = data_dir / "milvus.db"

    # Convert the Path object to a string and prepend the URI scheme
    milvus_uri = f"{milvus_db_path}"

    # Define a schema
    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),  # Primary key field
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=128),  # Vector field with dimension 128
    ]
    schema = CollectionSchema(fields, description="A sample collection")
    collection_name = "example_collection"

    # Create the collection
    with milvus_client(milvus_uri) as client:
        if not client.has_collection(collection_name=collection_name):
            client.create_collection(collection_name=collection_name, schema=schema)

        app = DocumentChat()
        app.run()
