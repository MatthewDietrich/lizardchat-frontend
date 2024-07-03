import flet as ft

from views.channel import ChannelView
from views.home import HomeView


def main(page: ft.Page) -> None:
    page.title = "IRC Client"
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    home_view = HomeView()
    channel_view = ChannelView("#main_chat")

    def route_change(e: ft.RouteChangeEvent) -> None:
        page.views.clear()
        page.views.append(home_view)
        match page.route:
            case "/channel":
                page.views.append(channel_view)
        page.update()

    page.on_route_change = route_change
    page.go("/channel")


ft.app(target=main)
