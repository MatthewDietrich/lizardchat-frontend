import select
import socket
from random import randint
from typing import Self


class IrcUser:
    def __init__(self, nick: str, username: str, host: str, realname: str = None):
        self.nick = nick
        self.username = username
        self.host = host
        self.realname = realname

    def __str__(self) -> str:
        return f"<User nick={self.nick} username={self.username}>"

    def __repr__(self) -> str:
        return f"{self.nick}!{self.username}@{self.host}"

    def __bytes__(self) -> bytes:
        return bytes(repr(self), "utf-8")

    @classmethod
    def from_raw(cls, raw: str) -> Self:
        """Construct a User from raw IRC server user string"""
        try:
            nick, remaining = raw.split("!")
            username, host = remaining.split("@")
            return cls(nick, username, host)
        except ValueError as exc:
            raise ValueError("Invalid user string " + raw) from exc


class IrcMessage:
    def __init__(self, source: IrcUser | None, command: str, params: str) -> None:
        self.source = source
        self.command = command
        self.params = params

    def __str__(self) -> str:
        return f"<Message source={self.source} command={self.command}>"

    def __repr__(self) -> str:
        if isinstance(self.source, IrcUser):
            source = repr(self.source)
        else:
            source = self.source
        return (
            f'{":" + source + " " if self.source else ""}'
            f"{self.command} {self.params}\r\n"
        )

    def __bytes__(self) -> bytes:
        return bytes(repr(self), "utf-8")

    @classmethod
    def from_raw(cls, raw: str) -> Self:
        """Construct a Message object from raw IRC server output"""
        stripped = raw.strip("\r\n")
        try:
            if stripped.startswith("@"):
                raise NotImplementedError("This client currently does not support tags")
            elif stripped.startswith(":"):
                src, cmd, *params = stripped.split(" ")
                src = src[1:]
                try:
                    src = IrcUser.from_raw(src)
                except ValueError:
                    pass
            else:
                src = None
                cmd, *params = stripped.split(" ")
            return cls(src, cmd, " ".join(params))
        except ValueError as exc:
            raise ValueError("Invalid message string " + raw) from exc


class IrcBaseClient:
    def __init__(self, nick: str, username: str, password: str = None) -> None:
        self.nick = nick
        self.password = password
        self.username = username
        self.socket = None
        self.connected = False

    def connect(self, hostname: str, port: int = 6667) -> None:
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.connect((hostname, port))
        self.socket.settimeout(10)

        if self.password:
            self.send(IrcMessage(None, "PASS", self.password))
        self.send(IrcMessage(None, "NICK", self.nick))
        self.send(IrcMessage(None, "USER", f"{self.username} 0 * :{self.username}"))

        while True:
            message = self.get_message()
            if message:
                print(repr(message).strip())
                match message.command:
                    case "005":
                        break
                    case "433":  # Nickname already in use
                        self.send(
                            IrcMessage(None, "NICK", f"{self.nick}_{randint(10, 99)}")
                        )
                        break

        self.connected = True

    def send(self, message: IrcMessage) -> None:
        raw = bytes(message)
        self.socket.send(raw)

    def get_message(self) -> IrcMessage | None:
        readable, _, _ = select.select([self.socket], [], [], 0)
        if readable:
            # Read reply one byte at a time
            reply = b""
            while c := self.socket.recv(1):
                reply = reply + c
                if c == b"\n":
                    message = IrcMessage.from_raw(reply.decode("utf-8"))
                    if message.command == "PING":
                        self.pong(message.params[1:])
                        return None
                    return message

    def get_all_messages(self) -> list[IrcMessage]:
        messages = []
        while message := self.get_message():
            messages.append(message)
        return messages

    def join(self, channel: str) -> None:
        self.send(IrcMessage(None, "JOIN", channel))

    def part(self, channel: str, reason: str) -> None:
        self.send(IrcMessage(None, "PART", f"{channel} {reason}"))

    def send_private_message(self, to: str, text: str) -> None:
        self.send(IrcMessage(None, "PRIVMSG", f"{to} {text}"))

    def send_notice(self, message_target: str, text: str) -> None:
        self.send(IrcMessage(None, "NOTICE", f"{message_target} {text}"))

    def get_names(self, channel: str) -> None:
        self.send(IrcMessage(None, "NAMES", channel))

    def pong(self, s: str) -> None:
        self.send(IrcMessage(None, "PONG", s))

    def query_topic(self, channel: str) -> None:
        self.send(IrcMessage(None, "TOPIC", channel))

    def set_topic(self, channel: str, topic: str) -> None:
        self.send(IrcMessage(None, "TOPIC", f"{channel} {topic}"))

    def invite(self, nick: str, channel: str) -> None:
        self.send(IrcMessage(None, "INVITE", f"{nick} {channel}"))

    def kick(self, channel: str, nick: str, comment: str) -> None:
        self.send(IrcMessage(None, "KICK", f"{channel} {nick} {comment}"))

    def motd(self) -> None:
        self.send(IrcMessage(None, "MOTD", ""))

    def version(self) -> None:
        self.send(IrcMessage(None, "VERSION", ""))

    def oper(self, name: str, password: str) -> None:
        self.send(IrcMessage(None, "OPER", f"{name} {password}"))

    def disconnect(self, message: str = "Quitting") -> None:
        self.send(IrcMessage(None, "QUIT", message))
        self.socket.shutdown(socket.SHUT_RDWR)
        self.socket.close()
        self.connected = False
