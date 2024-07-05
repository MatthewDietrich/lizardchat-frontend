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
        self.chat_input.on_submit = self.chat_submit
        self.active_buffer = "#lizardchatwebtest"
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
        self.user_list.set_nicks([self.page.session.get("nickname")])
        self.page.on_view_pop = lambda _: self.confirm_logout()
        self.join(self.active_buffer)
        self.page.update()

    def chat_submit(self, e: ft.ControlEvent) -> None:
        if self.chat_input.value:
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
        button.on_click = lambda _: self.set_active_buffer(buffer_name)
        self.buffer_buttons.add_button(button)

    def join(self, channel_name: str) -> None:
        self.add_buffer(channel_name)
        self.chat_output.set_active_buffer(channel_name)
        self.irc_client.client.join(channel_name)

    def set_active_buffer(self, buffer_name: str) -> None:
        self.active_buffer = buffer_name
        self.chat_output.set_active_buffer(buffer_name)
        self.page.update()

    def add_message_to_buffer(self, buffer_name: str, message: str):
        nick, *content = message.split(" ")
        self.chat_output.add_message_to_buffer(buffer_name, nick, " ".join(content))


class BufferButtons(ft.Row):
    def __init__(self) -> None:
        super().__init__()
        self.controls = []

    def add_button(self, button: ft.TextButton) -> None:
        self.controls.append(button)


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
        self.add_message("squam", "Hello world!")
        self.add_message("beavis", "Hehehe")

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
        self.nicks = []
        self.padding = 10
        self.title_text = ft.Text(value="Users", weight=ft.FontWeight.BOLD)
        self.controls = [self.title_text]

    def set_nicks(self, nicks: list[str]) -> None:
        self.nicks = sorted(set(self.nicks), key=lambda s: s.casefold())
        self.controls = [self.title_text]
        for nick in self.nicks:
            self.controls.append(NickBox(nick))


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
