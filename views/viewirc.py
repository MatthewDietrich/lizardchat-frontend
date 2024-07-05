import datetime
from typing import TypeAlias

import flet as ft

from irc import replycodes
from irc.client import IrcBaseClient, IrcMessage


HandlerResponse: TypeAlias = tuple[str, str]


class ViewMessageHandlers:
    def __init__(self, client: IrcBaseClient, view: ft.View) -> None:
        self.client = client
        self.view = view

    def bounce(self, message: IrcMessage) -> HandlerResponse:
        _, *content = message.params.split(" ")
        content = " ".join(content)
        return ":server", f"<!> {content}"

    def privmsg(self, message: IrcMessage) -> HandlerResponse:
        to, *content = message.params.split(" ")
        content = " ".join(content)[1:]
        return to, f"< {message.source.nick}> {content}"

    def join(self, message: IrcMessage) -> HandlerResponse:
        channel = message.params[1:]
        self.client.get_names(channel)
        return channel, f"User joined {channel}"

    def part(self, message: IrcMessage) -> HandlerResponse:
        channel = message.params[1:]
        self.client.get_names(channel)
        return channel, f"User left {channel}"

    def users(self, message: IrcMessage) -> HandlerResponse:
        _, *content = message.params.split(" ")
        content = " ".join(content)
        return ":server", f"<!> {content[1:]}"

    def motd(self, message: IrcMessage) -> HandlerResponse:
        _, *content = message.params.split(" ")
        content = " ".join(content)
        return ":server", f"<!> {content[1:]}"

    def namreply(self, message: IrcMessage) -> HandlerResponse:
        _, _, _, *names = message.params.split(" ")
        if names:
            names[0] = names[0][1:]  # remove leading colon from first name
        # TODO: Update users box in view
        return "", ""

    def end_of_names(self, message: IrcMessage) -> HandlerResponse:
        _, content = message.params.split(":")
        return ":server", f"<!> {content}"

    def topic(self, message: IrcMessage) -> HandlerResponse:
        _, channel, *topic = message.params.split(" ")
        topic = " ".join(topic)
        # TODO: set topic in view
        return channel, "Topic changed"

    def topic_who_time(self, message: IrcMessage) -> HandlerResponse:
        prefix, timestamp = message.params.split(":")
        _, channel, actor, _ = prefix.split(" ")
        timestamp = datetime.datetime.fromtimestamp(int(timestamp)).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        return channel, f"Topic set by {actor} on {timestamp}"

    def luser(self, message: IrcMessage) -> HandlerResponse:
        _, count, *remaining = message.params.split(" ")
        remaining = " ".join(remaining)
        return ":server", f"<!> {count} {remaining[1:]}"

    def no_topic(message: IrcMessage) -> HandlerResponse:
        # TODO: blank topic in view
        return "", ""

    def quit(self, message: IrcMessage) -> HandlerResponse:
        nick = message.source.nick
        quit_message = message.params[1:]
        # TODO: Update users box in view
        return "", ""


class ViewIrcClient:
    def __init__(self, view: ft.View) -> None:
        nick = view.page.session.get("nickname")
        username = view.page.session.get("username")
        password = view.page.session.get("password")
        if nick is None:
            print("Warning: nickname not set")
            nick = "asdf"
            username = "lizardchat-web"
        self.view = view
        self.client = IrcBaseClient(nick, username, password)
        message_handlers = ViewMessageHandlers(self.client, view)
        self.message_handler_functions = {
            "PRIVMSG": message_handlers.privmsg,
            "JOIN": message_handlers.join,
            "PART": message_handlers.part,
            "TOPIC": message_handlers.topic,
            "QUIT": message_handlers.quit,
            replycodes.RPL_BOUNCE: message_handlers.bounce,
            replycodes.RPL_LUSERCLIENT: message_handlers.users,
            replycodes.RPL_LUSERME: message_handlers.users,
            replycodes.RPL_LOCALUSERS: message_handlers.users,
            replycodes.RPL_GLOBALUSERS: message_handlers.users,
            replycodes.RPL_MOTD: message_handlers.motd,
            replycodes.RPL_MOTDSTART: message_handlers.motd,
            replycodes.RPL_ENDOFMOTD: message_handlers.motd,
            replycodes.RPL_NAMREPLY: message_handlers.namreply,
            replycodes.RPL_ENDOFNAMES: message_handlers.end_of_names,
            replycodes.RPL_TOPIC: message_handlers.topic,
            replycodes.RPL_TOPICWHOTIME: message_handlers.topic_who_time,
            replycodes.RPL_LUSEROP: message_handlers.luser,
            replycodes.RPL_LUSERUNKNOWN: message_handlers.luser,
            replycodes.RPL_LUSERCHANNELS: message_handlers.luser,
            replycodes.RPL_NOTOPIC: message_handlers.no_topic,
        }
        self.current_buf_changed = False

    def handle_message(self, message: IrcMessage) -> None:
        try:
            handler = self.message_handler_functions[message.command]
            to, content = handler(message)
        except KeyError:
            print("Unhandled command", repr(message))
            to = ":server"
            content = f"<!> {message.command} {message.params}"
        if all([to, content]):
            self.view.chat_output.add_message(to, content)
            self.current_buf_changed = True

    async def listen(self) -> None:
        if self.client.connected:
            self.current_buf_changed = False
            for message in self.client.get_all_messages():
                self.handle_message(message)
        if self.current_buf_changed:
            self.view.page.update()
        self.view.page.run_task(self.listen)
