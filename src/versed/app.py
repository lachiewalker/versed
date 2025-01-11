import json
from platformdirs import user_data_dir
from pathlib import Path
from textual.app import App

from versed.screens.chat_screen import ChatScreen
from versed.screens.collection_add_screen import AddCollectionScreen
from versed.screens.collection_select_screen import SelectCollectionScreen
from versed.screens.key_add_screen import AddKeyScreen
from versed.screens.key_load_screen import LoadKeyScreen
from versed.screens.quit_screen import QuitScreen

from versed.google_auth_handler import GoogleAuthHandler
from versed.secret_handler import SecretHandler
from versed.vector_store import VectorStore


class DocumentChat(App):
    """Main app that pushes the ChatScreen on startup."""

    BINDINGS = [
        ("q", "request_quit", "Quit"),
        ("d", "toggle_dark", "Toggle dark mode")
    ]

    DEFAULT_COLLECTION_NAME = "DefaultCollection"

    def __init__(self, app_name: str) -> None:
        super().__init__()
        self.app_name = app_name

        data_dir = Path(user_data_dir(self.app_name))
        data_dir.mkdir(parents=True, exist_ok=True)

        self.auth_handler = GoogleAuthHandler(self.app_name)
        self.credentials = self.auth_handler.fetch_credentials()
        self.api_key = None

        self.vector_store = VectorStore(
            app=self,
            data_dir=data_dir,
            default_collection_name=DocumentChat.DEFAULT_COLLECTION_NAME,
            google_credentials=self.credentials
        )
        self.collection_names = self.vector_store.get_collection_names()
        self.stats = None

        self.mimetype_extensions = {
            "application/vnd.google-apps.document": ".gdoc",
            "application/vnd.google-apps.spreadsheet": ".gsheet",
            "application/vnd.google-apps.presentation": ".gslides",
            "application/vnd.google.colab": ".ipynb",
            "application/vnd.google-apps.folder": "",
            "application/pdf": ".pdf",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": ".xlsx",
            "application/vnd.openxmlformats-officedocument.presentationml.presentation": ".pptx",
            "text/plain": ".txt",
            "text/csv": ".csv",
            "text/x-python": ".py",
            "text/x-java-source": ".java",
            "text/x-c": ".c",
            "text/x-c++src": ".cpp",
            "text/javascript": ".js",
            "application/x-httpd-php": ".php",
            "text/html": ".html",
            "text/css": ".css",
            "application/json": ".json",
            "application/xml": ".xml",
            "application/x-shellscript": ".sh",
            "application/x-ruby": ".rb",
            "text/markdown": ".md",
            "application/x-perl": ".pl",
            "application/x-lua": ".lua",
            "text/x-go": ".go",
            "application/x-yaml": ".yaml",
            "application/x-tar": ".tar",
            "application/zip": ".zip",
            "application/x-7z-compressed": ".7z",
            "application/x-rar-compressed": ".rar",
            "application/gzip": ".gz",
        }

        self.devtools = None

    def on_ready(self) -> None:
        def select_key(key: str | None) -> None:
            if key:
                try:
                    secret_handler = SecretHandler(self.app_name)
                    api_key = secret_handler.load_api_key(key)
                    self.api_key = api_key
                    self.vector_store.initialise_openai_client(api_key)
                except:
                    self.log(f"Unable to load key '{key}'.")

        self.push_screen("load_key", select_key)

    async def on_mount(self) -> None:
        # Install screens with the necessary constructor arguments
        self.install_screen(ChatScreen(), name="chat")
        self.install_screen(AddKeyScreen(), name="add_key")
        self.install_screen(LoadKeyScreen(), name="load_key")
        self.install_screen(AddCollectionScreen(), name="add_collection")
        self.install_screen(SelectCollectionScreen(), name="select_collection")

        self.title = "Versed"

        self.push_screen("chat")

    def on_vector_store_update(self):
        self.collection_names = self.vector_store.get_collection_names()

    def action_request_quit(self) -> None:
        self.push_screen(QuitScreen())

    def action_toggle_dark(self) -> None:
        """Action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    try:
        app = DocumentChat("versed")
        app.run()
    finally:
        app.milvus_client.close()
