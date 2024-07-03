import datetime

import flet as ft

from helpers.colors import CustomColors


class ChannelView(ft.View):
    def __init__(self, channel: str) -> None:
        super().__init__()
        self.route = "/channel"
        self.channel = channel
        self.chat_output = ChatOutput()
        self.user_list = UserList()
        self.chat_input = ChatInput()
        self.chat_input.on_submit = self.chat_submit
        self.controls = [
            ft.AppBar(
                title=ft.Row(
                    [ft.Text(channel), ft.Image("images/lizard_icon_small.png")]
                ),
                bgcolor=CustomColors.NAVY,
            ),
            ft.ResponsiveRow(
                controls=[
                    ft.Column(controls=[self.user_list], col={"md": 1}),
                    ft.Column(
                        controls=[
                            ft.Container(
                                content=self.chat_output, bgcolor=CustomColors.BLACK
                            )
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
        if self.page.session.get("nickname") is None:
            print("Warning: nickname not set")
        self.login()
        self.user_list.add_nicks(["squam", "beavis", self.page.session.get("nickname")])
        self.page.on_view_pop = lambda _: self.confirm_logout()
        self.page.update()

    def chat_submit(self, e: ft.ControlEvent) -> None:
        if self.chat_input.value:
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
        pass

    def logout(self) -> None:
        pass


class ChatOutput(ft.ListView):
    def __init__(self) -> None:
        super().__init__()
        self.controls = []
        self.padding = 10
        self.height = 400
        self.auto_scroll = True
        self.on_scroll_interval = 0
        self.add_message("squam", "Hello world!")
        self.add_message("beavis", "Hehehe")

    def add_message(self, nick: str, message: str) -> None:
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.controls.append(ChatMessage(timestamp, nick, message))


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

    def add_nicks(self, nicks: list[str]) -> None:
        for nick in nicks:
            if nick:
                self.nicks.append(nick)
        self.nicks = sorted(self.nicks, key=lambda s: s.casefold())
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
        self.controls = [
            ft.Text(value=timestamp, size=10),
            ft.Text(value=f"{nickname}: ", weight=ft.FontWeight.BOLD),
            ft.Text(value=message, selectable=True),
        ]
