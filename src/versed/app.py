from textual.app import App

from screens.quit_screen import QuitScreen
from screens.chat_screen import ChatScreen
from screens.add_key_screen import AddKeyScreen
from screens.load_key_screen import LoadKeyScreen

from platformdirs import user_data_dir
from pathlib import Path
from pymilvus import MilvusClient, FieldSchema, DataType, CollectionSchema
from contextlib import contextmanager

from keys import ApiKeyHandler

@contextmanager
def milvus_client(uri):
    client = MilvusClient(uri=uri)
    try:
        yield client
    finally:
        client.close()


class DocumentChat(App):
    """Main app that pushes the ChatScreen on startup."""

    BINDINGS = [
        ("q", "request_quit", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode")
    ]

    def __init__(self, app_name) -> None:
        super().__init__()
        self.app_name = app_name
        self.api_key = None

        self.devtools = None

    def on_ready(self) -> None:

        def select_key(key: str | None) -> None:
            if key:
                try:
                    key_handler = ApiKeyHandler()
                    api_key = key_handler.load_api_key(key)
                    self.api_key = key
                except:
                    print(f"Unable to load key '{key}'.")

        self.push_screen("load_key", select_key)

    async def on_mount(self) -> None:
        # Install screens with the necessary constructor arguments
        self.install_screen(ChatScreen(), name="chat")
        self.install_screen(AddKeyScreen(), name="add_key")
        self.install_screen(LoadKeyScreen(), name="load_key")

        self.push_screen("chat")

    def action_request_quit(self) -> None:
        self.push_screen(QuitScreen())

    def action_toggle_dark(self) -> None:
        """Action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    APP_NAME = "versed"
    DATA_DIR = Path(user_data_dir(APP_NAME))
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    milvus_db_path = DATA_DIR / "milvus.db"
    milvus_uri = f"{milvus_db_path}"

    fields = [
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
        FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=128),
    ]
    schema = CollectionSchema(fields, description="A sample collection")
    collection_name = "example_collection"

    with milvus_client(milvus_uri) as client:
        if not client.has_collection(collection_name=collection_name):
            client.create_collection(collection_name=collection_name, schema=schema)

        app = DocumentChat(APP_NAME)
        app.run()
