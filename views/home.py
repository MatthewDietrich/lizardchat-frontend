import flet as ft

from helpers.colors import CustomColors


class HomeView(ft.View):
    def __init__(self) -> None:
        super().__init__()
        self.route = "/"
        self.text_nickname = ft.TextField(
            label="Nickname",
            text_align=ft.TextAlign.LEFT,
            width=200,
            on_change=self.validate,
        )
        self.text_password = ft.TextField(
            label="Password (optional, for registered nicknames)",
            text_align=ft.TextAlign.LEFT,
            width=200,
            password=True,
        )
        self.checkbox_agree = ft.Checkbox(
            label="I agree to follow the server rules",
            value=False,
            on_change=self.validate,
            width=200,
        )
        self.login_button = ft.ElevatedButton(
            text="Enter the Chat",
            scale=1.5,
            on_click=self.submit,
            disabled=True,
        )
        self.rules_button = ft.TextButton(text="View Rules", on_click=self.show_rules)
        self.back_button = ft.TextButton(
            text="Back to Main Site", url="https://lizard.fun"
        )
        self.controls = [
            ft.AppBar(
                title=ft.Row(
                    [ft.Text("Login"), ft.Image("/images/lizard_icon_small.png")]
                ),
                bgcolor=CustomColors.NAVY,
            ),
            ft.Text(
                spans=[
                    ft.TextSpan(text="Welcome to "),
                    ft.TextSpan(
                        text="Lizardnet", style=ft.TextStyle(color=CustomColors.SEAFOAM)
                    ),
                ],
                size=36,
            ),
            self.text_nickname,
            self.text_password,
            self.checkbox_agree,
            self.login_button,
            self.rules_button,
            self.back_button,
        ]
        self.vertical_alignment = ft.MainAxisAlignment.CENTER
        self.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        self.spacing = 26

    def validate(self, e: ft.ControlEvent) -> None:
        self.login_button.disabled = not (
            self.text_nickname.value and self.checkbox_agree.value
        )
        self.page.update()

    def submit(self, e: ft.ControlEvent) -> None:
        self.page.session.set("nickname", self.text_nickname.value)
        self.page.session.set("password", self.text_password.value)
        self.page.session.set("username", f"lizardchat-web")
        self.page.session.set("realname", f"lizardchat-web")
        self.page.go("/chat")

    def show_rules(self, e: ft.ControlEvent) -> None:
        with open("assets/text/rules.txt", "r") as f:
            rules_text = f.read()
        rules_dialog = ft.AlertDialog(
            content=ft.Text(rules_text),
            actions=[
                ft.TextButton(text="Ok", on_click=lambda _: self.page.close_dialog())
            ],
        )
        self.page.show_dialog(rules_dialog)
