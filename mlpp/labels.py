"""Module to implement a label stack
- a label is a string used to represent a position
- labels are grouped """


from typing import Dict, List


class LabelStackError(ValueError):
	"""Abstract class for LabelStackErrors"""


class EmptyLabelStack(LabelStackError):
	"""raised when trying to add/retrive labels
	from an EmptyStack"""


class TooShortLabelStack(LabelStackError):
	"""Raised when trying to collapse an
	empty or 1-deep stack"""

class LabelStack:
	"""a stack of labels,
	each layer contains position relative
	to the start of the current string being parsed"""

	_stack: List[Dict[str, List[int]]]

	def __init__(self: "LabelStack") -> None:
		"""initializes label stack"""
		self._stack = []

	@property
	def height(self: "LabelStack") -> int:
		"""The height of the stack, should match
		Preprocessor._recursion_depth"""
		return len(self._stack)

	@property
	def top_level(self: "LabelStack") -> Dict[str, List[int]]:
		"""Returns the top level of the stack"""
		if self.height == 0:
			raise EmptyLabelStack("Canno't access toplevel of an empty stack")
		return self._stack[-1]

	def add_label(self: "LabelStack", label: str, pos: int) -> None:
		"""Adds a label to the toplevel
		pos should be relative to the string start (i.e. Position.relative_XXX)
		"""
		toplevel = self.top_level
		if label in toplevel:
			toplevel[label].append(pos)
		else:
			toplevel[label] = [pos]

	def get_label(self: "LabelStack", label: str) -> List[int]:
		"""returns a list of positions of label on the current level"""
		toplevel = self.top_level
		if label in toplevel:
			return toplevel[label]
		return []

	def new_level(self: "LabelStack") -> None:
		"""Adds a new label level"""
		self._stack.append(dict())

	def pop_level(self: "LabelStack", offset: int) -> None:
		"""Collapses a level
		offset is the position of the start of toplevel string
		relative to the start of the previous one"""
		if self.height < 2:
			raise TooShortLabelStack("Label Stack height should be at least 2 to pop a level")
		for label in self._stack[-1]:
			offset_pos = [pos + offset for pos in self._stack[-1][label]]
			if label in self._stack[-2]:
				self._stack[-2][label].extend(offset_pos)
			else:
				self._stack[-2][label] = offset_pos
		del self._stack[-1]

	def forget_level(self: "LabelStack") -> None:
		"""Forgets the topmost level and returns to the previous one"""
		if self.height == 0:
			raise EmptyLabelStack("Canno't forget level on empty stack")
		del self._stack[-1]

	@staticmethod
	def _dilate_list(lst: List[int], pos: int, value: int) -> List[int]:
		"""returns the dilated list"""
		new_list = []
		for val in lst:
			if val > pos:
				new_list.append(val + value)
			else:
				new_list.append(val)
		return new_list

	def dilate_level(self: "LabelStack", level: int, pos: int, value: int) -> None:
		"""dilates a level (used to signal an insertion/deletion)
		level is the level to dilate (should be preprocessor._recursion_depth)
		  can be -1 for topmost level
		pos it the position where insertion/deletion takes place
		value is the value of the dilatation (positive for insertion, negative for deletion)
		"""
		if self.height == 0:
			raise EmptyLabelStack("Cannot dilate level in empty stack")
		if -self.height >= level or level >= self.height:
			raise IndexError("height should be between {} and {}, got {}".format(
				-self.height+1, self.height-1, level
			))
		new_level = dict()
		for label in self._stack[level]:
			new_level[label] = self._dilate_list(self._stack[level][label], pos, value)
		self._stack[level] = new_level

	def copy(self: "LabelStack") -> "LabelStack":
		"""returns and independent copy of self"""
		new = LabelStack()
		new._stack = [level.copy() for level in self._stack]
		return new
