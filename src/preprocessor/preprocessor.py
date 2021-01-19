"""
Definitions of the actual Preprocessor class
"""
import re
from sys import stderr
from typing import Any, Callable, Dict, List, Tuple

from .context import ContextStack, FileDescriptor
from .defs import *
from .labels import LabelStack

TokenList = List[Tuple[int, int, TokenMatch]]
TypeCommand = Callable[["Preprocessor", str], str]
TypeBlock = Callable[["Preprocessor", str, str], str]
TypeFinalAction = Callable[["Preprocessor", str], str]

class Preprocessor:
	"""This class implements the preprocessor:

	Useful attributes that can be configured:
	- max_recursion_depth: int (default 20) - raises an error past this depth
	- token_begin and token_end: str (default "{% " and " %}")
	    use these to change the token used around preprocessor calls
	    in the document.
	    They should not be equal or be a simple double quote " or paranthese ( or )
	- token_endblock: str (default "end")
	    Used to specify what form the endblock command takes
	    (with the regex <token_begin>\\s*<token_endblock><block_name>\\s*<token_end>)
	- safe_calls: bool (default True)
	    if True, catches exceptions raised by command or blocks
	- error_mode: ErrorMode (default RAISE)
	    | PRINT_AND_EXIT -> print to stderr and exit
	    | PRINT_AND_RAISE -> print to stderr and raise exception
	    | RAISE -> raise exception"
	- warning_mode: WarningMode (default RAISE)
      | HIDE -> do nothing
      | PRINT -> print to stderr
      | RAISE -> raise python warning
      | AS_ERROR -> passes to self.send_error()
	"""

	# constants
	max_recursion_depth: int = 20
	token_begin: str = "{% "
	token_end: str = " %}"
	token_endblock: str = "end"
	re_flags: int = re.MULTILINE
	exit_code: int = 2
	safe_calls: bool = True

	# change to warnings and error to remove ansi sequences
	warning_str: str = "\033[35mwarning\033[39m"
	error_str: str   = "\033[31merror\033[39m"

	# warning and error modes
	error_mode: ErrorMode = ErrorMode.RAISE
	warning_mode: WarningMode = WarningMode.RAISE

  # if True, warning when finding unmatch token_end
	warn_unmatch_close: bool = False

	# private attributes
	_recursion_depth: int
	_final_actions: List[Tuple[int, RunActionAt, TypeFinalAction]] = []

	# commands and blocks
	commands: Dict[str, TypeCommand] = dict()
	blocks: Dict[str, TypeBlock] = dict()
	command_vars: Dict[str, Any] = dict()

	# useful variables
	labels: LabelStack
	context: ContextStack
	current_position: Position
	include_path: List[str]


	def __init__(self):
		self.commands = Preprocessor.commands.copy()
		self.blocks = Preprocessor.blocks.copy()
		self._final_actions = Preprocessor._final_actions.copy()
		self.command_vars = Preprocessor.command_vars.copy()
		self.current_position = Position()
		self.context = ContextStack()
		self.labels = LabelStack()
		self._recursion_depth = -1
		self.include_path = list()

	def _print_stderr_msg(self: "Preprocessor", desc: str, msg: str) -> None:
		"""Pretty printing to stderr using self._context
		Inputs:
		 - desc should be "error" or "warning"
		 - msg the message to print"""
		msg = msg.replace("\n", "\n  ") # add indent to following lines
		print("{} {}: {}".format(self.context.trace(), desc, msg), file=stderr)

	def send_error(self: "Preprocessor", error_msg: str) -> None:
		"""Handles errors
		Inputs:
		  self - Preprocessor object
		  error_msg - string : an error message
		Effect:
		  if self.exit_on_error print message and exit
		  else raise an Exception
		"""
		if self.error_mode == ErrorMode.PRINT_AND_EXIT:
			self._print_stderr_msg(self.error_str, error_msg)
			exit(self.exit_code)
		if self.error_mode == ErrorMode.PRINT_AND_RAISE:
			self._print_stderr_msg(self.error_str, error_msg)
		raise Exception(error_msg)

	def send_warning(self: "Preprocessor", warning_msg: str) -> None:
		"""Handles warnings
		Inputs:
		  self - Preprocessor object
		  warning_msg - string : the warning message
		Effect:
		  Depends on self.warning_mode:
		  | HIDE -> do nothing
		  | PRINT -> print to stderr
			| PRINT_AND_RAISE -> print to stderr and raise warning
		  | RAISE -> raise python warning
		  | AS_ERROR -> passes to self.send_error()
		"""
		if self.warning_mode == WarningMode.PRINT or self.warning_mode == WarningMode.PRINT_AND_RAISE:
			self._print_stderr_msg(self.warning_str, warning_msg)
		if self.warning_mode == WarningMode.RAISE or self.warning_mode == WarningMode.PRINT_AND_RAISE:
			raise Warning(warning_msg)
		if self.warning_mode == WarningMode.AS_ERROR:
			self.send_error(warning_msg)

	def split_args(self: "Preprocessor", args: str) -> List[str]:
		"""Splits args along space like on the command line
		preserves strings
		ex: self.split_args(" foo -bar\\t "some string" escaped\\ space")
		    returns ["foo", "-bar", "some string", "escaped space"]"""
		arg_list: List[str] = []
		ii = 0
		last_blank = 0
		len_args = len(args)
		in_string = False
		while ii < len_args:
			if args[ii] == "\\":
				ii += 1
				if ii < len_args:
					# skip escaped character
					ii += 1
					continue
				else:
					break
			if in_string:
				if args[ii] == '"':
					in_string = False
					arg_list.append(process_string(args[last_blank + 1 : ii]))
					last_blank = ii + 1
			elif args[ii].isspace():
				if last_blank != ii:
					arg_list.append(args[last_blank:ii].replace("\\ ", " "))
				last_blank = ii + 1
			elif args[ii] == '"':
				in_string = True
			ii += 1
		# end while
		if in_string:
			self.send_error("Unterminated string \"... in arguments")
		if last_blank != ii:
			arg_list.append(args[last_blank:ii].replace("\\ ", " "))
		return arg_list

	def _find_tokens(self: "Preprocessor", string: str) -> TokenList:
		"""Find all tokens (begin/end) in string
		Inputs:
			string: str - the string to search for tokens
		Returns:
			tokens: List[int, TokenMatch] - list of (position, OPEN/CLOSE)
				sorted by position (CLOSE comes first if equal)
		"""
		open_tokens  = re.finditer(re.escape(self.token_begin), string, self.re_flags)
		close_tokens = re.finditer(re.escape(self.token_end), string, self.re_flags)
		tokens = [(x.start(), x.end(), TokenMatch.OPEN) for x in open_tokens]
		tokens += [(x.start(), x.end(), TokenMatch.CLOSE) for x in close_tokens]
		# sort in order of appearance - if two tokens appear at same place
		# sort CLOSE first
		tokens.sort(key=lambda x: x[0] + 0.5 * int(x[2]))
		return tokens

	@staticmethod
	def _find_matching_pair(tokens: TokenList) -> int:
		"""find the first innermost OPEN CLOSE pair in tokens
		Inputs:
		  tokens - list of tuples containing 4 elements
				tokens[i][3] should be a boolean indicating
				OPEN with True and CLOSE with False
				Assumed to be at least 2 elements long
		Returns:
      the first index i such that tokens[i][3] == True and tokens[i+1][3] == False
      -1 if no such index exists
		"""
		len_tokens = len(tokens)
		token_index = 0
		while (
			tokens[token_index][2] != TokenMatch.OPEN
			or tokens[token_index + 1][2] != TokenMatch.CLOSE
		):
			token_index += 1
			if token_index + 1 >= len_tokens:
				return -1
		return token_index

	def _find_matching_endblock(
		self: "Preprocessor", block_name: str, string: str
	) -> Tuple[int, int]:
		"""Finds the matching endblock
		i.e. the first enblock token in string that does not
		match a startblock token
		Inputs:
			block_name: str - the name of the block.
				it is used to determine the endblock and startblock tokens
			string: str - the string being parsed
		Returns:
			tuple(endblock_start_pos: int, endblock_end_pos: int)
			(-1,-1) if no such endblock exists"""
		endblock_regex = r"{}\s*{}{}\s*{}".format(
			re.escape(self.token_begin), re.escape(self.token_endblock),
			block_name, re.escape(self.token_end)
		)
		startblock_regex = r"{}\s*{}(?:{}|{})".format(
			re.escape(self.token_begin), block_name,
			re.escape(self.token_end), REGEX_IDENTIFIER_END
		)
		pos = 0
		open_block = 0
		match_begin = re.search(startblock_regex, string, self.re_flags)
		match_end = re.search(endblock_regex, string, self.re_flags)
		while True:
			if match_end is None:
				return -1, -1
			if match_begin is None:
				open_block -= 1
				if open_block == -1:
					return pos + match_end.start(), pos + match_end.end()
				pos += match_end.end()
			else:
				if match_begin.start() < match_end.start():
					open_block += 1
					pos += match_begin.end()
				else:
					open_block -= 1
					if open_block == -1:
						return pos + match_end.start(), pos + match_end.end()
					pos += match_end.end()
			match_begin = re.search(startblock_regex, string[pos:], self.re_flags)
			match_end = re.search(endblock_regex, string[pos:], self.re_flags)

	def replace_string(self: "Preprocessor",
		start: int, end: int, string: str, replacement: str, tokens: TokenList,
	) -> str:
		"""replaces string[start:end] with replacement
		also add offset to token requiring them
		Inputs:
			start, end - indexes of the string to replace (relative to start of string)
			string - the string in which to replace
			replacement - the replacement string to place between start and end
			tokens - list of tokens to add dilation
		Returns:
			str = string[:start] + replacement + string[end:]
		Effect:
			removes all tokens occuring between start and end from tokens
			corrects start and end of further tokens by the length change
		"""
		test_range = range(start, end)
		i = 0
		dilat = len(replacement) - (end - start)
		while i < len(tokens):
			if tokens[i][0] in test_range or tokens[i][1] in test_range:
				del tokens[i]
			else:
				if tokens[i][0] >= end:
					tokens[i] = (
						tokens[i][0] + dilat,
						tokens[i][1] + dilat,
						tokens[i][2],
					)
				i += 1
		self.context.add_dilatation(start, dilat)
		self.labels.dilate_level(self._recursion_depth, end, dilat)
		# only remove level if it wasn't explicitly removed
		if self.labels.height > self._recursion_depth + 1:
			self.labels.pop_level(start)
		return string[:start] + replacement + string[end:]

	def _remove_leading_close_tokens(self: "Preprocessor", tokens: TokenList) -> None:
		"""removes leading close tokens from tokens
		if self.warn_unmatch_close is true, issues a warning"""
		while tokens and tokens[0][2] == TokenMatch.CLOSE:
			del tokens[0]
			if self.warn_unmatch_close:
				self.send_warning("unmatch closing token \"{}\".".format(self.token_end))

	def safe_call(self: "Preprocessor", function, *args, **kwargs) -> str:
		"""safely calls function (returning string)
		catches exceptions and warnings"""
		if self.safe_calls:
			string = ""
			try:
				string = function(*args, **kwargs)
			except Warning as warn:
				self.send_warning("internal warning.\n" + str(warn))
			except Exception as error:
				self.send_error("internal error.\n" + str(error))
			return string
		return function(*args, **kwargs)

	def parse(self: "Preprocessor", string: str) -> str:
		"""parses the string, calling the command and blocks it contains
		calls post_actions when parsing is done
		Inputs:
			string - the string to parse
		Expects:
			self._context[-1][0] should contain a context describing the string
			self._context[-1][1] is used to determine offset between string and source
			  (for error display)
		Returns:
			the resulting string"""
		# Recursion check
		self._recursion_depth += 1
		if self._recursion_depth == self.max_recursion_depth:
			self.send_error("recursion depth exceeded.")
		# add label level if none present
		if self.labels.height <= self._recursion_depth:
			self.labels.new_level()
		# context init
		empty_context = False
		if self.context.is_empty():
			self.context.new(FileDescriptor("NO FILE", ""), 0)
			self.current_position.offset = 0
			empty_context = True
		else:
			self.current_position.offset = self.context.top.position

		tokens: TokenList = self._find_tokens(string)

		# save original length to avoid deleting preexisting actions
		nb_actions = len(self._final_actions.copy())

		while len(tokens) > 1:  # needs two tokens to make a pair

			# find innermost (nested pair)
			token_index = self._find_matching_pair(tokens)
			if token_index == -1:
				self.send_error("no matching open/close pair found")

			self.current_position.relative_begin = tokens[token_index][0]
			self.current_position.relative_cmd_begin = tokens[token_index][1]
			self.current_position.relative_cmd_end = tokens[token_index+1][0]
			self.current_position.relative_end = tokens[token_index+1][1]
			substring = string[
				self.current_position.relative_cmd_begin : self.current_position.relative_cmd_end
			]
			ident, arg_string, i = get_identifier_name(substring)
			self.current_position.relative_cmd_argbegin = i
			end_pos = self.current_position.relative_end
			self.context.update(self.current_position.begin)
			new_str = ""
			position = self.current_position.copy()
			if ident == "":
				self.send_error("invalid command name: \"{}\".".format(substring))
			elif ident in self.commands:
				self.context.update(self.current_position.cmd_begin, "in command {}".format(ident))
				command = self.commands[ident]
				new_str = self.safe_call(command, self, arg_string)
				self.context.pop()
			elif ident in self.blocks:
				endblock_b, endblock_e = self._find_matching_endblock(
					ident, string[self.current_position.relative_end:]
				)
				if endblock_b == -1:
					self.send_error('no matching endblock for {} block.'.format(ident))
				self.current_position.endblock_begin = endblock_b + self.current_position.end
				self.current_position.endblock_end = endblock_e + self.current_position.end
				block_content = string[
					self.current_position.relative_end : self.current_position.relative_endblock_begin
				]
				end_pos = self.current_position.relative_endblock_end
				block = self.blocks[ident]

				self.context.update(self.current_position.cmd_begin, "in block {}".format(ident))

				new_str = self.safe_call(block, self, arg_string, block_content)

				self.context.pop()
			else:
				self.send_error("undefined command or block: \"{}\".".format(ident))
			self.current_position = position
			self.context.pop()
			string = self.replace_string(
				self.current_position.relative_begin, end_pos, string, new_str, tokens
			)
			self._remove_leading_close_tokens(tokens)
		# end while
		if len(tokens) == 1:
			self.send_error(
				'Unmatched "{}" token.\nAdd matching "{}" or use "{}begin{}" to place it.'.format(
					self.token_begin, self.token_end, self.token_begin, self.token_end
				)
			)

		string = self._handle_final_actions(nb_actions, string)

		self._recursion_depth -= 1
		if self._recursion_depth == -1:
			self.labels = LabelStack()
		if empty_context:
			self.context = ContextStack()
		return string

	def _handle_final_actions(self: "Preprocessor", nb_preserved_actions: int, string: str) -> str:
		"""handles final actions: run those at current level
		and then removes those that shouldn't propagate upwards
		nb_preserved action is the number of action to keep (inherited from parent)"""
		self.context.update(self.current_position.from_relative(0), "in final actions")
		new_actions = []
		for i, (level, run_at, action) in enumerate(self._final_actions):
			# run action
			if self._runs_at_current_level(level, run_at):
				string = self.safe_call(action, self, string)
			# keep relevant action only
			if i < nb_preserved_actions or bool(run_at & RunActionAt.PARRALLEL_CHILDREN):
				new_actions.append((level, run_at, action))
			elif bool(run_at & RunActionAt.STRICT_PARENT_LEVELS):
				new_actions.append((level - 1, run_at, action))
		self._final_actions = new_actions
		self.context.pop()
		return string

	def _runs_at_current_level(self: "Preprocessor", level: int, run_at: RunActionAt) -> bool:
		"""return True if this action should be run at the current recursion level"""
		return (level == self._recursion_depth and bool(run_at & RunActionAt.CURRENT_LEVEL)) \
		  or (level < self._recursion_depth and bool(run_at & RunActionAt.STRICT_SUB_LEVELS)) \
		  or (level > self._recursion_depth and bool(run_at & RunActionAt.STRICT_PARENT_LEVELS))

	@staticmethod
	def static_add_finalaction(
		action: TypeFinalAction, run_at: RunActionAt = RunActionAt.CURRENT_LEVEL
	) -> None:
		"""adds a final action to the base class, will be a part of all new objects"""
		Preprocessor._final_actions.append((0, run_at, action))

	def add_finalaction(self: "Preprocessor", action: TypeFinalAction,
		run_at: RunActionAt = RunActionAt.CURRENT_LEVEL
	) -> None:
		"""adds a final action at the current level"""
		self._final_actions.append((self._recursion_depth, run_at, action))

	def get_help(self: "Preprocessor", help_msg: str) -> str:
		"""used to get and display help on the command line
		help_msg is either:
			""         -> display program help
			"commands" -> list all commands and blocks
			<cmd_name> -> display help relative to a command or block
		returns the help string
		"""
		if help_msg == "":
			return trim("""
				{name} version {version}
				Simple program to preprocess files inspired by the C preprocessor

				Files to process can contain:
				 - preprocessor commands "{begin}command_name [args]{end}"
				 - preprocessor blocks "{begin}block_name [args]{end}... {begin}endblock_name{end}"
				A list of commands and blocks can be obtained with "--help commands"

				Usage: {name} [--flags] [input_file]
				  default input_file is stdin

				Options:
				  -o --output <file>   specifies a file to write output to
				                       default is stdout
				  -w --warnings <hide|error> choose whether to hide warnings
				                       or have them raise an error. default is display
				  -b --begin <string>  change the begin token (default is "{begin}")
				  -e --end <string>    change the end token (default is "{end}")
				  -d -D --define <name>[=<value>] defines a simple command
				                       with name <name> which prints <value> (nothing if no value)
				                       Can be used multiple times on command line
				  -i -I --include <path> Adds paths to the INCLUDE_PATH.
					                     default INCLUDE_PATH is [".", dir(input_file), dir(output_file)]
				                       Can be used multiple times on command line
				  -v --version         show version and exit
				  -h --help            show this help and exit
				  -h --help "commands" show a list of commands and blocks and exit
				  -h --help <cmd_name> show help for a specific command of block
				""".format(
					name = PREPROCESSOR_NAME, version = PREPROCESSOR_VERSION,
					begin = "{% ", end = " %}"))
		if help_msg == "commands":
			return "Commands:\n  " + "\n  ".join(sorted(self.commands.keys())) +\
				"\n\nBlocks:\n  " + "\n  ".join(sorted(self.blocks.keys()))
		if help_msg in self.commands or help_msg in self.blocks:
			cmd: Any
			if help_msg in self.commands:
				cmd = self.commands[help_msg]
				cmd_type = "command"
			else:
				cmd = self.blocks[help_msg]
				cmd_type = "block"
			if hasattr(cmd, "doc"):
				doc = cmd.doc
			else:
				doc = cmd.__doc__
			doc = "  " + trim(doc).replace("\n", "\n  ")
			if doc == "":
				doc = "No help available"
			return "{}: help on {} {}:\n{}".format(
				PREPROCESSOR_NAME, cmd_type, help_msg, doc
			)
		return "{} help:\nUnknown command of block \"{}\"".format(PREPROCESSOR_NAME, help_msg)
