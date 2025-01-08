import asyncio
from platformdirs import user_data_dir
from pathlib import Path
from pymilvus import MilvusClient, FieldSchema, DataType, CollectionSchema
from textual.app import App

from versed.screens.key_add_screen import AddKeyScreen
from versed.screens.chat_screen import ChatScreen
from versed.screens.docs_screen import DocsScreen
from versed.screens.key_load_screen import LoadKeyScreen
from versed.screens.quit_screen import QuitScreen

from versed.google_auth_handler import GoogleAuthHandler
from versed.secret_handler import SecretHandler


class DocumentChat(App):
    """Main app that pushes the ChatScreen on startup."""

    BINDINGS = [
        ("q", "request_quit", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode"),
        ("v", "view_docs", "View Documents")
    ]

    def __init__(self, app_name: str) -> None:
        super().__init__()
        self.app_name = app_name

        data_dir = Path(user_data_dir(self.app_name))
        data_dir.mkdir(parents=True, exist_ok=True)

        milvus_db_path = data_dir / "milvus.db"
        self.milvus_uri = f"{milvus_db_path}"

        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=128),
        ]
        schema = CollectionSchema(fields, description="A sample collection")
        self.collection_name = "example_collection"

        self.milvus_client = MilvusClient(uri=self.milvus_uri)
        if not self.milvus_client.has_collection(collection_name=self.collection_name):
            self.milvus_client.create_collection(collection_name=self.collection_name, schema=schema)

        self.auth_handler = GoogleAuthHandler(self.app_name)
        self.credentials = self.auth_handler.fetch_credentials()
        self.api_key = None

        self.stats = None

        self.devtools = None

    def on_ready(self) -> None:
        def select_key(key: str | None) -> None:
            if key:
                try:
                    secret_handler = SecretHandler(self.app_name)
                    api_key = secret_handler.load_api_key(key)
                    self.api_key = api_key
                except:
                    self.log(f"Unable to load key '{key}'.")

        self.push_screen("load_key", select_key)

    async def on_mount(self) -> None:
        # Install screens with the necessary constructor arguments
        self.install_screen(ChatScreen(), name="chat")
        self.install_screen(AddKeyScreen(), name="add_key")
        self.install_screen(LoadKeyScreen(), name="load_key")
        self.install_screen(DocsScreen(), name="docs")

        self.title = "Versed"

        self.push_screen("chat")

    def action_request_quit(self) -> None:
        self.push_screen(QuitScreen())

    def action_toggle_dark(self) -> None:
        """Action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    async def action_view_docs(self) -> None:
        """
        Fetches stats about the vector collection and displays them in a modal screen.
        """
        results = self.milvus_client.get_collection_stats(self.collection_name)
        self.stats = results

        # Push the modal screen with retrieved documents
        await self.push_screen("docs")


if __name__ == "__main__":
    try:
        app = DocumentChat("versed")
        app.run()
    finally:
        app.milvus_client.close()
