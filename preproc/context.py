"""This module is used to traceback error to file positions

It contains:

- class FileDescriptor
	contains info about a file (name, contents and linebreaks)

- class ContextElement
	stores a current context with
	- a FileDescriptor (file to point back to when reporting errors)
	- a position
	- a description
	- a list of dilatations that account for insertion/deletions

- class ContextStack:
	a stack of ContextElements
	add elements on top with .new() or .update()
	remove them with .pop()
	.trace() shows a trace leading to the topmost context
"""

import re
from typing import List, Optional, Tuple


class FileDescriptor:
	"""describes a file,
	contains:
	- file name
	- file initial contents
	- line breaks"""

	filename: str
	contents: str
	_line_breaks: List[int]

	def __init__(self: "FileDescriptor", filename: str, contents: str) -> None:
		"""initialises the FileDescriptor element and computes linebreaks"""
		self.filename = filename
		self.contents = contents
		self._line_breaks = self.line_breaks_from_str(contents)

	@staticmethod
	def line_breaks_from_str(string: str) -> List[int]:
		"""Generates a list of line break indices from a given string
		i.e. return L containing all index i such that
		string[i] == "\\n"
		"""
		return [n.start() for n in re.finditer(re.escape("\n"), string)]

	def line_number(self: "FileDescriptor", pos: int) -> Tuple[int, int]:
		"""Returns a tuple (line number, char number on line)
		from an absolute position"""
		line_nb = 1
		closest_line_end = 0
		for line_end in self._line_breaks:
			if line_end <= pos:
				line_nb += 1
				if pos - line_end < pos - closest_line_end:
					closest_line_end = line_end
		return line_nb, pos - closest_line_end


class ContextElement:
	"""Context for error tracing
	stores:
	- file names
	- line breaks (to recover line number)
	- dilatations (how are indexes shifted by insertions/deletions)
	It is used to recover the initial position for error traceback"""

	file: FileDescriptor
	description: str
	position: int
	is_new: bool
	_dilatations: List[Tuple[int, int]]

	def __init__(
		self: "ContextElement", file: FileDescriptor, desc: str, pos: int, is_new: bool = True
	) -> None:
		"""initializes a new ContextElement"""
		self.file = file
		self.description = desc
		self.position = pos
		self.is_new = is_new
		self._dilatations = []

	def true_position(self: "ContextElement", position: int) -> int:
		"""Returns the true position, taking dilatations
		into account"""
		for pos, value in self._dilatations[::-1]:
			if pos <= position:
				position -= value
		return position

	def add_dilatation(self: "ContextElement", pos: int, value: int) -> None:
		"""Adds a dilatation, i.e. indicates that
		position after pos are increased/decreased by value
		Ex when changing "bar foo bar" to "bar newfoo bar"
		  add a dilatation (pos = 4, value = len("newfoo") - len("foo"))
		"""
		if value != 0:
			self._dilatations.append((pos, value))

	def copy(self: "ContextElement", position: int, desc: Optional[str] = None) -> "ContextElement":
		"""returns a copy of self"""
		if desc is None:
			desc = self.description
		copy = ContextElement(self.file, desc, position, False)
		for pos, value in self._dilatations:
			copy.add_dilatation(pos, value)
		return copy


class EmptyContextStack(ValueError):
	"""Exception raised when context stack
	is empty"""


class ContextStack:
	"""Class used to store context information to print in traceback"""
	_stack: List[ContextElement]

	def __init__(self: "ContextStack", stack: List[ContextElement] = []) -> None:
		"""initializes a new context stack"""
		self._stack = stack

	@property
	def top(self: "ContextStack") -> ContextElement:
		"""returns the top element
		raises EmptyContextStack if empty"""
		if not self.is_empty():
			return self._stack[-1]
		raise EmptyContextStack

	def new(self: "ContextStack", file: FileDescriptor, pos: int, desc: str = "") -> None:
		"""adds context relative to a new file on top of the stack
		pos should be the position relative to the start of the file
		desc is an optional description string (ex "in command my_command")"""
		self._stack.append(ContextElement(file, desc, pos))

	def update(self: "ContextStack", pos: int, desc: Optional[str] = None) -> None:
		"""adds a new context element based on the previous one on top of the stack
		pos: position relative to start of file
		desc: optional string description"""
		self._stack.append(self.top.copy(pos, desc))

	def pop(self: "ContextStack") -> None:
		"""removes the topmost Context from the stack"""
		if self._stack:
			del self._stack[-1]
		else:
			raise EmptyContextStack

	def add_dilatation(self: "ContextStack", pos: int, value: int) -> None:
		"""Adds a dilatation to topmost context.
		It indicates that positions after pos are increased/decreased by value
		Ex when changing "bar foo bar" to "bar newfoo bar"
		  add a dilatation (pos = 4, value = len("newfoo") - len("foo"))"""
		self.top.add_dilatation(pos, value)

	def trace(self: "ContextStack") -> str:
		"""Returns a string trace for error solving.
		It is in the format:
		"path/to/file:line:char: desc
		path/to/topmost/file:line:char: topmost desc
		path/to/topmost/file:line:char:"
		"""
		trace = ""
		stack_size = len(self._stack)
		for i, elem in enumerate(self._stack):
			if i + 1 == stack_size or self._stack[i+1].is_new:
				line, char = elem.file.line_number(elem.true_position(elem.position))
				trace += "{}:{}:{}: {}\n".format(
					elem.file.filename, line, char, elem.description
				)
		if self._stack:
			elem = self.top
			line, char = elem.file.line_number(elem.true_position(elem.position))
			trace += "{}:{}:{}:".format(elem.file.filename, line, char)
		else:
			trace += "EMPTY STACK:"
		return trace


	def is_empty(self: "ContextStack") -> bool:
		"""returns True if stack is empty, False otherwise"""
		return self._stack == []
