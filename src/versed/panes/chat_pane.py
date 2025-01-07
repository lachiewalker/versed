from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.events import Resize
from textual.widgets import (
    Button,
    Label,
    Static,
    TextArea
)

from openai import OpenAI


class ChatPane(Container):
    """Pane with a chat window and text input stacked vertically."""

    DEFAULT_CSS = """
    #messages-window {
        height: 80%;
        background: $background;
        border: none;
        padding: 0 0 1 0;
        overflow: auto scroll;
    }

    #placeholder-label {
        height: 100%;
        width: 100%;
        color: $text-disabled;
        content-align: center middle;
    }

    .user-message, .bot-message {
        width: auto;
        height: auto;
        padding: 1;
        margin: 1;
    }

    .user-message {
        background: $secondary;
    }

    .bot-message {
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

    def __init__(self) -> None:
        super().__init__()
        self.client = OpenAI(api_key=self.app.api_key)
    
    def compose(self) -> ComposeResult:
        # Top 80% container: Scrollable chat messages
        with VerticalScroll(id="messages-window"):
            yield Label("Ask a query...", id="placeholder-label")

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
        """
        Dynamically adjust child widget sizes when the container is resized.
        """
        def dynamic_size_input_bar():
            input_container = self.query_one("#input-container")
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

            response = await self.generate_bot_response(user_query)
            
            await self.add_message(response, False)

    @on(Button.Pressed, "#clear")
    def clear_input(self) -> None:
        pass

    async def add_message(self, text: str, is_user: bool) -> None:
        """
        Add a message to the scrollable container.
        """
        placeholder_label = self.query_one("#placeholder-label")
        placeholder_label.styles.display = "none"

        message_window = self.query_one("#messages-window")

        message_class = "user-message" if is_user else "bot-message"
        message_box = Static(text.strip(), classes=message_class)

        message_window.mount(message_box)
        message_window.scroll_end()

    async def generate_bot_response(self, user_message: str) -> str:
        """
        Generate bot response.
        """
        response = self.client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            model="gpt-4o",
        )
        
        assistant_message = response.choices[0].message.content
        return assistant_message
