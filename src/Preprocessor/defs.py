#!/usr/bin/python3
# -*- coding: utf-8 -*-
from enum import Enum, IntEnum

REGEX_IDENTIFIER: str = "[_a-zA-Z][_a-zA-Z0-9]*"
REGEX_IDENTIFIER_END: str = "$|[^_a-zA-Z0-9]"
REGEX_STRING: str = '""|".*?[^\\\\]"'


class Position:
	"""represents a position to a command
	#1{% #2cmd#3 args#4 %}#5...#6{% endcmd %}#7
	- #1 - begin
	- #2 - cmd_begin
	- #3 - cmd_argbegin
	- #4 - cmd_end
	- #5 - end
	#6 and #7 values are meaningless if not a block
	- #6 - endblock_begin
	- #7 - endblock_end"""
	begin:          int = 0
	end:            int = 0
	cmd_begin:      int = 0
	cmd_end:        int = 0
	cmd_argbegin:   int = 0
	endblock_begin: int = 0
	endblock_end:   int = 0


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


def process_string(string: str) -> str:
	"""Change escape sequences to the chars they match
	ex: process_string("\\\\n") -> "\\n\""""
	return string.encode().decode("unicode-escape")
