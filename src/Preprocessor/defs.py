#!/usr/bin/python3
# -*- coding: utf-8 -*-
import enum
import re
from typing import Callable, List, Tuple, Union, cast

REGEX_IDENTIFIER:       str = "[_a-zA-Z][_a-zA-Z0-9]*"
REGEX_IDENTIFIER_END:   str = "$|[^_a-zA-Z0-9]"
REGEX_IDENTIFIER_BEGIN: str = "^|[^_a-zA-Z]"
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
	- #7 - endblock_end
	these values are relative to the start of the string
	being scanned. For values relative to the start of the source
	(namely for errors and context updates) use the methods
	true_begin(), true_end()...

	offset represents the offset between current string and source"""
	offset: int = 0

	begin:          int = 0
	end:            int = 0
	cmd_begin:      int = 0
	cmd_end:        int = 0
	cmd_argbegin:   int = 0
	endblock_begin: int = 0
	endblock_end:   int = 0

	true_begin: Callable[["Position"], int] = \
		lambda self: self.begin + self.offset
	true_end: Callable[["Position"], int] = \
		lambda self: self.end + self.offset
	true_cmd_begin: Callable[["Position"], int] = \
		lambda self: self.cmd_begin + self.offset
	true_cmd_end: Callable[["Position"], int] = \
		lambda self: self.cmd_end + self.offset
	true_cmd_argbegin: Callable[["Position"], int] = \
		lambda self: self.cmd_argbegin + self.offset
	true_endblock_begin: Callable[["Position"], int] = \
		lambda self: self.endblock_begin + self.offset
	true_endblock_end: Callable[["Position"], int] = \
		lambda self: self.endblock_end + self.offset


class EmptyContextStack(Exception):
	pass


class WarningMode(enum.Enum):
	HIDE = 1
	PRINT = 2
	RAISE = 3
	AS_ERROR = 4


class TokenMatch(enum.IntEnum):
	OPEN = 0
	CLOSE = 1


class Context:

	file: str = ""
	desc: str = ""
	_line_breaks: List[int] = []
	_dilatations: List[Tuple[int, int]] = []

	def __init__(self: "Context", file: str,
		line_breaks: Union[List[int], str], desc: str = ""
	) -> None:
		"""Creates a context object
		Inputs:
		  file: str - the file path or equivalent
      line_breaks: Union[List[int], str] - used to determine line numbers from a position
			  if a List[int], represents the positions of line breaks in file
				  can be generated with Context.line_breaks_from_str() or
					[n.start() for n in re.finditer(re.escape("\\n"), file_contents)]
				if a str, it should be the file contents (or have linebreaks in the same places)
			desc: str (default "") - a description (ex "in command my_command")
		"""
		self.file = file
		if isinstance(line_breaks, list):
			self._line_breaks = line_breaks
		else:
			self._line_breaks = self.line_breaks_from_str(line_breaks)
		self.desc = desc
		self._dilatations = []

	@staticmethod
	def line_breaks_from_str(string: str) -> List[int]:
		"""Generates a list of line break indices from a given string
		i.e. return L containing all index i such that
		string[i] == "\\n"
		"""
		return [n.start() for n in re.finditer(re.escape("\n"), string)]

	def add_dilatation(self: "Context", pos: int, value: int) -> None:
		"""Adds a dilatation, i.e. indicates that
		position after pos are increased/decreased by value
		Ex when changing "bar foo bar" to "bar newfoo bar"
		  add a dilatation (pos = 4, value = len("newfoo") - len("foo"))
		"""
		self._dilatations.append((pos, value))

	def true_position(self: "Context", position: int) -> int:
		"""Returns the true position, taking dilatations
		into account"""
		for pos, value in self._dilatations[::-1]:
			if pos < position:
				position -= value
		return position

	def line_number(self: "Context", pos: int) -> Tuple[int, int]:
		"""Returns a tuple (line number, char number on line)
		from a pos (taking dilatations into account)"""
		true_pos = self.true_position(pos)
		line_nb = 1
		closest_line_end = 0
		for line_end in self._line_breaks:
			if line_end <= true_pos:
				line_nb += 1
				if true_pos - line_end < true_pos - closest_line_end:
					closest_line_end = line_end
		return line_nb, true_pos - closest_line_end

	def copy(self: "Context") -> "Context":
		"""returns a copy of self sharing _line_break and _dilatations
		but not desc"""
		copy = Context(self.file, self._line_breaks, self.desc)
		copy._dilatations = self._dilatations
		return copy


NO_CONTEXT = Context("", [], "")

def process_string(string: str) -> str:
	"""Change escape sequences to the chars they match
	ex: process_string("\\\\n") -> "\\n\""""
	return string.encode().decode("unicode-escape")
