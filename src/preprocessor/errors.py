"""
File containing error classes and methods for error handling

It defines:
- enum WarningMode and ErrorMode used to configure the Preprocessor
- class PreprocessorErrorWarningBase containing info about an Error/Warning
- class PreprocessorError(Exception, PreprocessorErrorWarningBase)
  used to raise errors
- class PreprocessorWarning(Warning, PreprocessorErrorWarningBase)
  used to raise warning
"""

import enum

from .context import ContextStack

ANSI_ERROR   = "\033[31m" # red
ANSI_WARNING = "\033[35m" # purple
ANSI_RESET   = "\033[39m"

@enum.unique
class WarningMode(enum.Enum):
	"""Preprocessor warning modes:
	| HIDE -> do nothing
	| PRINT -> print to stderr
	| PRINT_AND_RAISE -> print to stderr and raise warning
	| RAISE -> raise python warning
	| AS_ERROR -> passes to send_error()"""
	HIDE = 1
	PRINT = 2
	PRINT_AND_RAISE = 3
	RAISE = 4
	AS_ERROR = 5


@enum.unique
class ErrorMode(enum.Enum):
	"""Preprocessor error modes:
	| PRINT_AND_EXIT -> print to stderr and exit
	| PRINT_AND_RAISE -> print to stderr and raise exception
	| RAISE -> raise exception"""
	PRINT_AND_EXIT = 1
	PRINT_AND_RAISE = 2
	RAISE = 3


class PreprocessorErrorWarningBase:
	"""standard preprocessor error/warning class
	PreprocessorError and PreprocessorWarning both inherit from this.
	Attributes:
	- name (ex : "missing-endblock")
	- message (ex: "no matching endblock for ...")
	- context: ContextStack (file pos)
	- trace (ex: "filename:line:char: context_msg...")
	"""

	name: str
	message: str
	context: ContextStack
	is_error: bool

	def __init__(
		self: "PreprocessorErrorWarningBase",
		name: str, message: str, context: ContextStack, is_error: bool
	) -> None:
		"""Initializes the object:
		Arguments:
		- name (ex : "missing-endblock")
		- message (ex: "no matching endblock for ...")
		- context: ContextElement (file pos)
		- is_error: false if warning
		"""
		self.name = name
		self.message = message
		self.context = context
		self.is_error = is_error

	@property
	def position(self: "PreprocessorErrorWarningBase") -> int:
		"""the true position (number of characters from start of file)"""
		return self.context.top.true_position(self.context.top.position)

	@property
	def line(self: "PreprocessorErrorWarningBase") -> int:
		"""The line number of the error"""
		return self.context.top.file.line_number(self.position)[0]

	@property
	def char(self: "PreprocessorErrorWarningBase") -> int:
		"""The number of characters from the start of the line"""
		return self.context.top.file.line_number(self.position)[1]

	@property
	def filename(self: "PreprocessorErrorWarningBase") -> str:
		"""The name of the file"""
		return self.context.top.file.filename

	def format_name(self: "PreprocessorErrorWarningBase") -> str:
		"""formats name into -Wname or -Ename
		depending on self.is_error"""
		if self.is_error:
			return "-E"+self.name
		return "-W"+self.name

	def format_message(self: "PreprocessorErrorWarningBase", ansi :bool = False) -> str:
		"""formats the message into
		first line [-Wname/-Ename]
		following lines"""
		msg = self.message.split("\n")
		if ansi:
			if self.is_error:
				msg[0] += " [{}{}{}]".format(ANSI_ERROR, self.format_name(), ANSI_RESET)
			else:
				msg[0] += " [{}{}{}]".format(ANSI_WARNING, self.format_name(), ANSI_RESET)
		else:
			msg[0] += " [{}]".format(self.format_name())
		return "\n".join(msg)

	def __str__(self: "PreprocessorErrorWarningBase") -> str:
		"""transform self into string for error display
		ex: filename:line:char: message [name]"""
		return "{}:{}:{}: {}".format(
			self.filename, self.line, self.char, self.format_message()
		)

	def pretty_message(self: "PreprocessorErrorWarningBase", ansi: bool = False) -> str:
		"""pretty prints self with trace, use ansi if specified"""
		trace = self.context.trace()
		if self.is_error:
			err = "error:"
			if ansi:
				err = ANSI_ERROR + err + ANSI_RESET
		else:
			err = "warning:"
			if ansi:
				err = ANSI_WARNING + err + ANSI_RESET
		return "{} {} {}".format(trace, err, self.format_message(ansi).replace("\n", "\n  "))



class PreprocessorError(PreprocessorErrorWarningBase, Exception):
	"""The standard class for preprocessor errors"""
	def __init__(
		self: "PreprocessorError", name: str, message: str, context: ContextStack
	) -> None:
		"""Initializes the object:
		Arguments:
		- name (ex : "missing-endblock")
		- message (ex: "no matching endblock for ...")
		- context: ContextElement (file pos)
		"""
		PreprocessorErrorWarningBase.__init__(self, name, message, context, True)
		Exception.__init__(self, PreprocessorErrorWarningBase.__str__(self))

class PreprocessorWarning(PreprocessorErrorWarningBase, Warning):
	"""The standard class for preprocessor warnings"""
	def __init__(
		self: "PreprocessorWarning", name: str, message: str, context: ContextStack
	) -> None:
		"""Initializes the object:
		Arguments:
		- name (ex : "missing-endblock")
		- message (ex: "no matching endblock for ...")
		- context: ContextElement (file pos)
		"""
		PreprocessorErrorWarningBase.__init__(self, name, message, context, False)
		Warning.__init__(self, PreprocessorErrorWarningBase.__str__(self))
