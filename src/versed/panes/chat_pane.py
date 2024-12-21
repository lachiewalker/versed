from textual.app import ComposeResult
from textual import on
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.widgets import (
    TextArea,
    Button,
    Label,
    Static
)
from textual.events import Resize


class UserMessage(Container):

    DEFAULT_CSS = """
    #chat-message {
        height: auto;
        align: left top;
        background: $secondary;
        padding: 1;
        margin: 1;
    }

    #message {
        align-horizontal: left;
        width: 70%;
        height: auto;
    }
    """
    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()

    def compose(self) -> ComposeResult:
        with Horizontal(id="chat-message"):
            self.text_area = Static(self.text, id="message")
            yield self.text_area


class ChatPane(Container):
    """The right pane with a vertical split and input field at the bottom."""

    DEFAULT_CSS = """
    #messages-window {
        height: 80%;
        background: $background;
        border: none;
        padding: 0 0 1 0;
        overflow: auto scroll;
    }

    .message_container {
        height: auto
    }

    #placeholder-label {
        height: 100%;
        width: 100%;
        align: center middle;
        color: $text-disabled;
    }

    .user-message, .bot-message {
        width: 70%;
        height: auto;
        padding: 1;
        margin: 1;
    }

    .user-message {
        align-vertical: top;
        align-horizontal: left;
        background: $secondary;
    }

    .bot-message {
        align-vertical: top;
        align-horizontal: right;
        background: $panel;
    }

    #input-container {
        height: 20%;
        width: 100%;
        padding: 0 1 1 1;
    }

    #text-area {
        border: none;
        box-sizing: border-box;
        margin: 0 1 0 0;
    }

    #send {
        width: 6;
        height: 3;
        min-width: 4;
        box-sizing: border-box;
        margin: 0;
        border: none;
        text-align: center;
        background: $primary;
    }
    #send:focus {
        text-style: bold;
    }

    #clear {
        width: 6;
        height: 1;
        min-width: 4;
        box-sizing: border-box;
        margin: 1 0 0 0;
        border: none;
        text-align: center;
        background: $warning-darken-1;
    }
    #clear:focus {
        text-style: bold;
    }
    """

    BINDINGS = [
        ('shift+tab', 'send_message', 'Send')
    ]
    
    def compose(self) -> ComposeResult:
        # Top 80% container: Scrollable space
        yield VerticalScroll(id="messages-window")
            # yield Label("Ask a query...", id="placeholder-label")

        # Bottom 20% container: Text input and buttons
        with Horizontal(id="input-container"):
            self.text_area = TextArea(id="text-area")
            yield self.text_area
            with Vertical(id="buttons-container"):
                self.send_button = Button("Send", id="send")
                yield self.send_button
                self.clear_button = Button("CLR", id="clear")
                yield self.clear_button


    def on_resize(self, event: Resize) -> None:
        """Dynamically adjust child widget sizes when the container is resized."""
        # Get the width of the parent container
        def dynamic_size_input_bar():
            input_container = self.app.query_one("#input-container")
            parent_width = input_container.size.width

            send_button_width = 6 + 1   # Width for the Send button + spacer
            text_area_width = max(0, parent_width - send_button_width)

            self.text_area.styles.width = text_area_width

        dynamic_size_input_bar()


    @on(Button.Pressed, "#send")
    async def action_send_message(self) -> None:
        input_field = self.query_one("#text-area")
        user_query = input_field.text
        if user_query:
            await self.add_message(user_query, True)
            input_field.clear()

            response = f"Responding..."
            
            await self.add_message(response, False)


    @on(Button.Pressed, "#clear")
    def clear_input(self) -> None:
        pass


    async def add_message(self, text: str, is_user: bool) -> None:
        """Add a message to the scrollable container."""
        # placeholder_label = self.query_one("#placeholder-label")
        placeholder_label = self.query("#placeholder-label")
        # placeholder_label.styles.display = "none"
        if placeholder_label:
            placeholder_label.remove()

        message_window = self.query_one("#messages-window")
        # message_window.remove(placeholder_label)

        if is_user:
            message_class = "user-message"
            message_box = Static(text, classes=message_class)
            height = message_box.styles.height
            # message_box.styles.align_horizontal = "left"
            message_container = Horizontal(
                message_box,
                classes="message-container"
            )
            message_container.styles.height = height
            # message_box = UserMessage(text)

        else:
            message_class = "bot-message"
            message_box = Static(text, classes=message_class)
            height = message_box.styles.height
            # message_box.styles.align_horizontal = "right"
            message_container = Horizontal(
                message_box,
                classes="message-container"
            )
            message_container.styles.height = height

        message_window.mount(message_container)
        message_window.scroll_visible()

    # async def generate_bot_response(self, user_message: str) -> str:
    #     """Simulate bot response logic (replace with actual logic)."""
    #     # Placeholder bot response logic
    #     return f"Echo: {user_message}"
