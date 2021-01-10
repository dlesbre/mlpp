# -*- coding: utf-8 -*-
import argparse
import enum
import re
from typing import Tuple

PREPROCESSOR_NAME = "preprocessor"
PREPROCESSOR_VERSION = "0.1"

REGEX_IDENTIFIER:       str = "[_a-zA-Z][_a-zA-Z0-9]*"
REGEX_IDENTIFIER_WRAPPED: str = "(^|(?<=([^_a-zA-Z0-9]))){}((?=([^_a-zA-Z0-9]))|$)"
REGEX_IDENTIFIER_END:   str = "$|[^_a-zA-Z0-9]"
REGEX_IDENTIFIER_BEGIN: str = "^|[^_a-zA-Z]"
REGEX_STRING: str = '""|".*?[^\\\\]"'
REGEX_INTEGER: str = r"-?\ *[0-9]+(?:[_0-9]*[0-9])?"


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
	- #7 - endblock_end
	these values are relative to the start of the source file
	being scanned. For values relative to the start of the string
	use relative_begin, relative_end...

	offset represents the offset between current string and source"""
	offset: int = 0

	begin:          int = 0
	end:            int = 0
	cmd_begin:      int = 0
	cmd_end:        int = 0
	cmd_argbegin:   int = 0
	endblock_begin: int = 0
	endblock_end:   int = 0

	def to_relative(self: "Position", value: int) -> int:
		"""transform a value relative to source into one relative to current string"""
		return value - self.offset

	def from_relative(self: "Position", value: int) -> int:
		"""transform a value relative to current string into one relative to source"""
		return value + self.offset

	relative_begin: property = property(
		lambda self: self.to_relative(self.begin),
		lambda self, value: setattr(self, "begin", self.from_relative(value)),
		doc="same as begin, but relative to start of current parsed string\n"
		    "(begin is relative to start of file)"
	)
	relative_end: property = property(
		lambda self: self.to_relative(self.end),
		lambda self, value: setattr(self, "end", self.from_relative(value)),
		doc="same as end, but relative to start of current parsed string\n"
		    "(end is relative to start of file)"
	)
	relative_cmd_begin: property = property(
		lambda self: self.to_relative(self.cmd_begin),
		lambda self, value: setattr(self, "cmd_begin", self.from_relative(value)),
		doc="same as cmd_begin, but relative to start of current parsed string\n"
		    "(cmd_begin is relative to start of file)"
	)
	relative_cmd_end: property = property(
		lambda self: self.to_relative(self.cmd_end),
		lambda self, value: setattr(self, "cmd_end", self.from_relative(value)),
		doc="same as cmd_end, but relative to start of current parsed string\n"
		    "(cmd_end is relative to start of file)"
	)
	relative_cmd_argbegin: property = property(
		lambda self: self.to_relative(self.cmd_argbegin),
		lambda self, value: setattr(self, "cmd_argbegin", self.from_relative(value)),
		doc="same as cmd_argbegin, but relative to start of current parsed string\n"
		    "(cmd_argbegin is relative to start of file)"
	)
	relative_endblock_begin: property = property(
		lambda self: self.to_relative(self.endblock_begin),
		lambda self, value: setattr(self, "endblock_begin", self.from_relative(value)),
		doc="same as endblock_begin, but relative to start of current parsed string\n"
		    "(endblock_begin is relative to start of file)"
	)
	relative_endblock_end: property = property(
		lambda self: self.to_relative(self.endblock_end),
		lambda self, value: setattr(self, "endblock_end", self.from_relative(value)),
		doc="same as endblock_end, but relative to start of current parsed string\n"
		    "(endblock_end is relative to start of file)"
	)

	def copy(self:"Position") -> "Position":
		"""creates an independent copy"""
		new = Position()
		new.offset = self.offset
		new.begin = self.begin
		new.end = self.end
		new.cmd_begin = self.cmd_begin
		new.cmd_end = self.cmd_end
		new.cmd_argbegin = self.cmd_argbegin
		new.endblock_begin = self.endblock_begin
		new.endblock_end = self.endblock_end
		return new


@enum.unique
class WarningMode(enum.Enum):
	"""Preprocessor warning modes:
	| HIDE -> do nothing
	| PRINT -> print to stderr
	| RAISE -> raise python warning
	| AS_ERROR -> passes to send_error()"""
	HIDE = 1
	PRINT = 2
	RAISE = 3
	AS_ERROR = 4


@enum.unique
class TokenMatch(enum.IntEnum):
	"""Used to represent Open/Closed tokens"""
	OPEN = 0
	CLOSE = 1


class RunActionAt(enum.IntFlag):
	"""Used to determine where to queue post actions
	(at current, sublevels and/or parent levels)"""
	NO_LEVEL = 0
	CURRENT_LEVEL = enum.auto()
	STRICT_SUB_LEVELS = enum.auto()
	STRICT_PARENT_LEVELS = enum.auto()
	PARRALLEL_CHILDREN = enum.auto()
	CURRENT_AND_SUB_LEVELS = CURRENT_LEVEL | STRICT_SUB_LEVELS
	CURRENT_AND_PARENT_LEVELS = CURRENT_LEVEL | STRICT_PARENT_LEVELS
	ALL_LEVELS = CURRENT_LEVEL | STRICT_PARENT_LEVELS | STRICT_SUB_LEVELS


def process_string(string: str) -> str:
	"""Change escape sequences to the chars they match
	ex: process_string("\\\\n") -> "\\n\""""
	return string.encode().decode("unicode-escape")


class ArgumentParserNoExit(argparse.ArgumentParser):
	"""subclass of argparse.ArgumentParser which
	raises an error rather than exiting when parsing fails"""
	def error(self, message):
		raise argparse.ArgumentError(None, message)


def get_identifier_name(string: str) -> Tuple[str, str, int]:
	"""finds the first identifier in string:
	Returns:
		tuple str, str, int - identifier, rest_of_string, start_of_rest_of_string
		returns ("","", -1) if None found"""
	match = re.match(
		r"\s*({})({}.*$)".format(REGEX_IDENTIFIER, REGEX_IDENTIFIER_END),
		string, re.DOTALL
	)
	if match is None:
		return ("", "", -1)
	return match.group(1), match.group(2), match.start(2)


def is_integer(string: str) -> bool:
	"""returns True if string can safely be converted
	to a integer with to_integer(string)"""
	return re.match(REGEX_INTEGER, string.strip()) is not None

def to_integer(string: str) -> int:
	"""converts string to integer"""
	return int(string.strip().replace(" ", "").replace("_", ""))
