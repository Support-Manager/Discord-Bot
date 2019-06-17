from enum import Enum, IntEnum


class Scope(Enum):
    PRIVATE = "private"
    LOCAL = "local"
    CHANNEL = "channel"


class State(Enum):
    OPEN = "open"
    CLOSED = "closed"
    REOPENED = "reopened"
    DELETED = "deleted"


class Language(Enum):
    ENGLISH = "EN"
    EN = "EN"

    GERMAN = "DE"
    DEUTSCH = "DE"
    DE = "DE"

    NORWEGIAN = "NO"
    NO = "NO"


class TitleLength(IntEnum):
    MIN = 5
    MAX = 100


class PrefixLength(IntEnum):
    MIN = 1
    MAX = 3
