#!/usr/bin/python3
from enum import Enum, IntEnum


REGEX_IDENTIFIER: str = "[_a-zA-Z][_a-zA-Z0-9]*"
REGEX_STRING: str = '""|".*?[^\\\\]"'


class Position:
	file: str = "stdin"
	line: int = 0
	char: int = 0

	def __init__(self: "Position", file: str, line: int, char: int) -> None:
		self.file = file
		self.line = line
		self.char = char


class CommandError(Exception):
	def __init__(self: "CommandError", position: Position, msg: str) -> None:
		self.pos: Position = position
		self.msg: str = msg


class WarningMode(Enum):
	HIDE = 1
	PRINT = 2
	RAISE = 3
	AS_ERROR = 4


class TokenMatch(IntEnum):
	OPEN = 0
	CLOSE = 1
