import asyncio
import datetime

import flet as ft

from views.viewirc import ViewIrcClient
from helpers.colors import CustomColors


class ChatView(ft.View):
    def __init__(self) -> None:
        super().__init__()
        self.route = "/chat"
        self.chat_output = ChatOutput()
        self.user_list = UserList()
        self.chat_input = ChatInput()
        self.buffer_buttons = BufferButtons()
        self.topic_output = TopicOutput()
        self.chat_input.on_submit = self.chat_submit
        self.active_buffer = "<server>"
        self.appbar = ft.AppBar(
            title=ft.Row(
                [ft.Text(self.active_buffer), ft.Image("/images/lizard_icon_small.png")]
            ),
            bgcolor=CustomColors.NAVY,
        )
        self.controls = [
            ft.ResponsiveRow(
                controls=[
                    ft.Column(controls=[self.user_list], col={"md": 1}),
                    ft.Column(
                        controls=[
                            self.topic_output,
                            ft.Container(
                                content=self.chat_output, bgcolor=CustomColors.BLACK
                            ),
                            self.buffer_buttons,
                        ],
                        col={"md": 11},
                    ),
                ],
            ),
            ft.Row(controls=[self.chat_input]),
        ]
        self.vertical_alignment = ft.MainAxisAlignment.START
        self.horizontal_alignment = ft.CrossAxisAlignment.START
        self.spacing = 26

    def did_mount(self) -> None:
        super().did_mount()
        self.irc_client = ViewIrcClient(self)
        self.login()
        self.add_buffer("<server>")
        self.page.run_task(self.irc_client.listen)
        self.page.on_view_pop = lambda _: self.confirm_logout()
        self.join("#lizardchatwebtest")
        self.page.update()

    def chat_submit(self, e: ft.ControlEvent) -> None:
        if input_value := self.chat_input.value:
            if input_value.startswith("/"):
                command, *remaining = input_value.split(" ")
                match command:
                    case "/join":
                        if len(remaining) == 1:
                            self.join(remaining[0])
                    case "/part":
                        if len(remaining) == 1:
                            if remaining[0] != "<server>":
                                self.part(remaining[0], "")
                        elif len(remaining) >= 2:
                            channel, *reason = remaining
                            reason = " ".join(reason)
                            self.part(channel, reason)
                    case "/invite":
                        if len(remaining) == 2:
                            nick, channel = remaining
                            self.irc_client.client.invite(nick, channel)
                    case "/kick":
                        if len(remaining) >= 2:
                            channel, nick, *comment = remaining
                            comment = " ".join(comment)
                            self.irc_client.client.kick(channel, nick, comment)
                    case "/motd":
                        self.irc_client.client.motd()
                    case "/version":
                        self.irc_client.client.version()
            else:
                self.irc_client.client.send_private_message(
                    self.chat_output.active_buffer, self.chat_input.value
                )
                self.chat_output.add_message(
                    self.page.session.get("nickname"), self.chat_input.value
                )
            self.chat_input.value = ""
        self.chat_input.focus()
        self.page.update()

    def confirm_logout(self) -> None:
        def do_pop(e: ft.ControlEvent) -> None:
            self.logout()
            self.page.views.pop()
            top_view = self.page.views[-1]
            self.page.go(top_view.route)

        logout_modal = ft.AlertDialog(
            modal=True,
            title=ft.Text("Quit?"),
            content=ft.Text("Are you sure you want to quit?"),
            actions=[
                ft.TextButton("Yes", on_click=do_pop),
                ft.TextButton("No", on_click=lambda _: self.page.close_dialog()),
            ],
        )
        self.page.show_dialog(logout_modal)

    def login(self) -> None:
        self.irc_client.client.connect("irc.lizard.fun", 6667)

    def logout(self) -> None:
        self.irc_client.client.disconnect()

    def add_buffer(self, buffer_name) -> None:
        button = ft.TextButton(text=buffer_name)
        self.chat_output.register_buffer(buffer_name)
        self.user_list.register_buffer(buffer_name)
        self.topic_output.register_buffer(buffer_name)
        button.on_click = lambda _: self.set_active_buffer(buffer_name)
        self.buffer_buttons.add_button(button)

    def join(self, channel_name: str) -> None:
        self.add_buffer(channel_name)
        self.irc_client.client.join(channel_name)
        self.set_active_buffer(channel_name)
        self.page.update()
        self.page.run_task(self.set_buffer_after_delay)

    def part(self, channel_name: str, reason: str) -> None:
        self.irc_client.client.part(channel_name, reason)
        self.buffer_buttons.remove_button(channel_name)

    def start_whisper(self, nick: str) -> None:
        self.add_buffer(nick)
        self.set_active_buffer(nick)
        self.page.update()

    def set_active_buffer(self, buffer_name: str) -> None:
        self.active_buffer = buffer_name
        self.chat_output.set_active_buffer(buffer_name)
        self.user_list.set_active_buffer(buffer_name)
        self.topic_output.set_active_buffer(buffer_name)
        self.appbar.title = ft.Row(
            [ft.Text(self.active_buffer), ft.Image("/images/lizard_icon_small.png")]
        )
        self.page.update()

    def add_message_to_buffer(self, buffer_name: str, message: str) -> None:
        nick, *content = message.split(" ")
        self.chat_output.add_message_to_buffer(buffer_name, nick, " ".join(content))

    async def set_buffer_after_delay(self) -> None:
        await asyncio.sleep(1)
        self.set_active_buffer(self.active_buffer)
        self.page.update()


class BufferButtons(ft.Row):
    def __init__(self) -> None:
        super().__init__()
        self.controls = []

    def add_button(self, button: ft.TextButton) -> None:
        self.controls.append(button)

    def remove_button(self, buffer_name: str) -> None:
        self.controls = [
            button for button in self.controls if button.text != buffer_name
        ]


class ChatOutput(ft.ListView):
    def __init__(self) -> None:
        super().__init__()
        self.controls = []
        self.padding = 10
        self.height = 400
        self.auto_scroll = True
        self.on_scroll_interval = 0
        self.buffers = {"<server>": []}
        self.active_buffer = "<server>"

    def add_message(self, nick: str, message: str) -> None:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        chat_message = ChatMessage(timestamp, nick, message)
        self.buffers[self.active_buffer].append(chat_message)

    def register_buffer(self, buffer_name: str) -> None:
        self.buffers[buffer_name] = []

    def set_active_buffer(self, buffer_name: str) -> None:
        try:
            self.controls = self.buffers[buffer_name]
            self.active_buffer = buffer_name
        except KeyError:
            print("No buffer named", buffer_name)

    def add_message_to_buffer(self, buffer_name: str, nick: str, message: str) -> None:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        try:
            self.buffers[buffer_name].append(ChatMessage(timestamp, nick, message))
        except KeyError:
            print("No buffer named", buffer_name)


class NickBox(ft.Container):
    def __init__(self, nick: str) -> None:
        super().__init__()
        self.bgcolor = CustomColors.BLACK
        self.content = ft.Text(value=nick)
        self.on_hover = self.hover

    def hover(self, e: ft.HoverEvent) -> None:
        if e.data == "true":
            self.bgcolor = CustomColors.NAVY
        else:
            self.bgcolor = CustomColors.BLACK
        self.page.update()


class UserList(ft.ListView):
    def __init__(self) -> None:
        super().__init__()
        self.padding = 10
        self.title_text = ft.Text(value="Users", weight=ft.FontWeight.BOLD)
        self.controls = [self.title_text]
        self.active_buffer = "<server>"
        self.buffers = {"<server>": []}

    def register_buffer(self, buffer_name: str) -> None:
        self.buffers[buffer_name] = []

    def set_buffer_nicks(self, buffer_name: str, nicks: list[str]) -> None:
        nicks = sorted(nicks, key=lambda s: s.casefold())
        try:
            self.buffers[buffer_name] = [NickBox(nick) for nick in nicks]
        except KeyError:
            print("No buffer named", buffer_name)

    def set_active_buffer(self, buffer_name) -> None:
        try:
            self.controls = [self.title_text]
            for nick_box in self.buffers[buffer_name]:
                self.controls.append(nick_box)
            self.active_buffer = buffer_name
        except KeyError:
            print("No buffer named", buffer_name)


class ChatInput(ft.TextField):
    def __init__(self) -> None:
        super().__init__()
        self.expand = True


class ChatMessage(ft.Row):
    def __init__(self, timestamp: str, nickname: str, message: str) -> None:
        super().__init__()
        self.timestamp = timestamp
        self.nickname = nickname
        self.message = message
        self.vertical_alignment = ft.MainAxisAlignment.START
        self.alignment = ft.CrossAxisAlignment.START
        self.spacing = 5
        self.controls = [
            ft.Text(value=timestamp, size=10),
            ft.Text(
                value=f"{nickname}:", weight=ft.FontWeight.BOLD, font_family="Cousine"
            ),
            ft.Text(value=message, selectable=True, font_family="Cousine"),
        ]


class TopicOutput(ft.Container):
    def __init__(self) -> None:
        super().__init__()
        self.buffers = {
            "<server>": ft.Text(
                spans=[
                    ft.TextSpan(
                        text="Server Messages",
                        style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                    ),
                ]
            )
        }
        self.active_buffer = "<server>"
        self.content = self.buffers[self.active_buffer]

    def register_buffer(self, buffer_name: str) -> None:
        if buffer_name == "<server>":
            self.buffers[buffer_name] = ft.Text(
                spans=[
                    ft.TextSpan(
                        text="Server Messages",
                        style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                    ),
                ]
            )
        else:
            self.buffers[buffer_name] = ft.Text(value="")

    def set_buffer_topic(self, buffer_name: str, topic: str) -> None:
        print("setting topic for", buffer_name, "to", topic)
        try:
            self.buffers[buffer_name] = ft.Text(
                spans=[
                    ft.TextSpan(
                        text="Topic: ", style=ft.TextStyle(weight=ft.FontWeight.BOLD)
                    ),
                    ft.TextSpan(
                        text=topic, style=ft.TextStyle(weight=ft.FontWeight.NORMAL)
                    ),
                ]
            )
        except KeyError:
            print("No buffer named", buffer_name)

    def set_active_buffer(self, buffer_name) -> None:
        try:
            self.content = self.buffers[buffer_name]
            self.active_buffer = buffer_name
        except KeyError:
            print("No buffer named", buffer_name)
