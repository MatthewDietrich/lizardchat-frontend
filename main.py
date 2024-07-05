import flet as ft

from views.chat import ChatView
from views.home import HomeView


def main(page: ft.Page) -> None:
    page.title = "Lizardnet Webchat"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.fonts = {"Cousine": "/fonts/Cousine-Regular.ttf"}

    home_view = HomeView()
    chat_view = ChatView("#main_chat")

    def route_change(e: ft.RouteChangeEvent) -> None:
        page.views.clear()
        page.views.append(home_view)
        match page.route:
            case "/chat":
                page.views.append(chat_view)
        page.update()

    page.on_route_change = route_change
    page.go("/chat")


ft.app(target=main, assets_dir="assets")
