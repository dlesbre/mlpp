# -*- coding: utf-8 -*-
import re
from sys import stderr
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

from .defs import *

TokenList = List[Tuple[int, int, TokenMatch]]
TypeCommand = Callable[["Preprocessor", str], str]
TypeBlock = Callable[["Preprocessor", str, str], str]
TypePostaction = Callable[["Preprocessor", str], str]

class Preprocessor:

	# constants
	max_recursion_depth: int = 20
	token_begin: str = "{% "
	token_end: str = " %}"
	token_endblock: str = "end"
	token_ident: str = REGEX_IDENTIFIER
	token_ident_end: str = REGEX_IDENTIFIER_END
	re_flags: int = re.MULTILINE
	exit_code: int = 2

	# change to warnings and error to remove ansi sequences
	warning_str: str = "\033[35mwarning\033[39m"
	error_str: str   = "\033[31merror\033[39m"

	# if False raises an error
	# if True print to stderr and exit
	exit_on_error: bool = True

	# if True, handle warnings as errors
	warning_mode: WarningMode = WarningMode.PRINT
  # if True, warning when finding unmatch token_end
	warn_unmatch_close: bool = False

	# private attributes
	_recursion_depth: int = 0
	_context: List[Tuple[Context, int, bool]] = []

	# commands and blocks
	commands: Dict[str, TypeCommand] = dict()
	blocks: Dict[str, TypeBlock] = dict()
	post_actions: List[TypePostaction] = []
	labels: Dict[str, List[int]] = dict()

	# usefull variables
	current_position: Position = Position()
	command_vars: Dict[str, Any] = dict()

	def __init__(self):
		self.commands = Preprocessor.commands.copy()
		self.blocks = Preprocessor.blocks.copy()
		self.post_actions = Preprocessor.post_actions.copy()
		self.command_vars = Preprocessor.command_vars.copy()
		self._context = Preprocessor._context.copy()

	def _print_stderr_msg(self: "Preprocessor", desc: str, msg: str) -> None:
		"""Pretty printing to stderr using self._context
		Inputs:
		 - desc should be "error" or "warning"
		 - msg the message to print"""
		msg = msg.replace("\n", "\n  ") # add indent to following lines
		if self._context:
			len_ctxt = len(self._context)
			for i, ctxt_tu in enumerate(self._context):
				if i + 1 == len_ctxt or self._context[i+1][2]:
					ctxt = ctxt_tu[0]
					line_nb, char = ctxt.line_number(ctxt_tu[1])
					if ctxt.desc:
						print("{}:{}:{}: {}".format(
							ctxt.file, line_nb, char, ctxt.desc),
							file=stderr
						)
			print("{}:{}:{}: {}: {}".format(
				ctxt.file, line_nb, char, desc, msg),
				file=stderr
			)
		else:
			print(" {}: {}".format(desc, msg), file=stderr)

	def send_error(self: "Preprocessor", error_msg: str) -> None:
		"""Handles errors
		Inputs:
      self - Preprocessor object
      error_msg - string : an error message
		Effect:
      if self.exit_on_error print message and exit
      else raise an Exception
		"""
		if self.exit_on_error:
			self._print_stderr_msg(self.error_str, error_msg)
			exit(self.exit_code)
		else:
			raise Exception(error_msg)

	def send_warning(self: "Preprocessor", warning_msg: str) -> None:
		"""Handles errors
		Inputs:
      self - Preprocessor object
      warning_msg - string : the warning message
		Effect:
      Depends on self.warning_mode:
      | HIDE -> do nothing
      | PRINT -> print to stderr
      | RAISE -> raise python warning
      | AS_ERROR -> passes to self.send_error()
		"""
		if self.warning_mode == WarningMode.PRINT:
			self._print_stderr_msg(self.warning_str, warning_msg)
		elif self.warning_mode == WarningMode.RAISE:
			raise Warning(warning_msg)
		elif self.warning_mode == WarningMode.AS_ERROR:
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

	def get_identifier_name(self: "Preprocessor", string: str) -> Tuple[str, str, int]:
		"""finds the first identifier in string:
		Returns:
			tuple str, str, int - identifier, rest_of_string, start_of_rest_of_string
		  returns ("","", -1) if None found"""
		match_opt = re.match(r"\s*({})({}.*)".format(self.token_ident, self.token_ident_end), string)
		if match_opt == None:
			return ("", "", -1)
		match = cast(re.Match, match_opt)
		return match.group(1), match.group(2), match.start(2)

	def find_tokens(self: "Preprocessor", string: str) -> TokenList:
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

	def find_matching_pair(self: "Preprocessor", tokens: TokenList) -> int:
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

	def find_matching_endblock(
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
			re.escape(self.token_end), self.token_ident_end
		)
		pos = 0
		open_block = 0
		match_begin_opt = re.search(startblock_regex, string, self.re_flags)
		match_end_opt = re.search(endblock_regex, string, self.re_flags)
		while True:
			if match_end_opt == None:
				return -1, -1
			match_end = cast(re.Match, match_end_opt)
			if match_begin_opt == None:
				open_block -= 1
				if open_block == -1:
					return pos + match_end.start(), pos + match_end.end()
				pos += match_end.end()
			else:
				match_begin = cast(re.Match, match_begin_opt)
				if match_begin.start() < match_end.start():
					open_block += 1
					pos += match_begin.end()
				else:
					open_block -= 1
					if open_block == -1:
						return pos + match_end.start(), pos + match_end.end()
					pos += match_end.end()
			match_begin_opt = re.search(startblock_regex, string[pos:], self.re_flags)
			match_end_opt = re.search(endblock_regex, string[pos:], self.re_flags)

	def replace_string(self: "Preprocessor",
		start: int, end: int, string: str, replacement: str, tokens: TokenList,
	) -> str:
		"""replaces string[start:end] with replacement
		also add offset to token requiring them
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
		if self._context:
			self._context[-1][0].add_dilatation(start, dilat)
		for key in self.labels:
			index_list = self.labels[key]
			for i in range(len(index_list)):
				if index_list[i] >= end:
					index_list[i] += dilat

		return string[:start] + replacement + string[end:]

	def remove_leading_close_tokens(self: "Preprocessor", tokens: TokenList) -> None:
		"""removes leading close tokens from tokens
		if self.warn_unmatch_close is true, issues a warning"""
		while tokens and tokens[0][2] == TokenMatch.CLOSE:
			del tokens[0]
			if self.warn_unmatch_close:
				self.send_warning("Unmatch close token")

	def context_new(self: "Preprocessor", context: Context, pos: int) -> None:
		"""Adds a new context. This is used to traceback errors
		Inputs:
		  context object indicates file and description
		  pos is the relative (dilated) position in the file
		    (can be obtained from self.current_position)
		"""
		self._context.append((context, pos, True))

	def context_update(self: "Preprocessor", pos: int, desc: Optional[str] = None) -> None:
		"""Updates the current context
		can change the position and, optionnaly, the description
		"""
		if len(self._context) != 0:
			new_context = self._context[-1][0].copy()
			if isinstance(desc, str):
				new_context.desc = desc
			self._context.append((new_context, pos, False))
		else:
			raise EmptyContextStack

	def context_pop(self : "Preprocessor") -> None:
		"""Removes the last context_new of context_update
		from the _context stack"""
		if len(self._context) != 0:
			self._context.pop()
		else:
			raise EmptyContextStack

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
			self.send_error("recursion depth exceeded")

		# context init
		empty_context = False
		old_offset = self.current_position.offset
		if self._context == []:
			self.context_new(NO_CONTEXT, 0)
			self.current_position.offset = 0
			empty_context = True # used to remove added context when doe
		else:
			self.current_position.offset = self._context[-1][1]

		tokens: TokenList = self.find_tokens(string)

		# post_action init
		post_actions = self.post_actions.copy()

		while len(tokens) > 1:  # needs two tokens to make a pair

			# find innermost (nested pair)
			token_index = self.find_matching_pair(tokens)
			if token_index == -1:
				self.send_error("no matching open/close pair found")

			self.current_position.begin = tokens[token_index][0]
			self.current_position.cmd_begin = tokens[token_index][1]
			self.current_position.cmd_end = tokens[token_index+1][0]
			self.current_position.end = tokens[token_index+1][1]
			substring = string[
				self.current_position.cmd_begin : self.current_position.cmd_end
			]
			ident, arg_string, i = self.get_identifier_name(substring)
			self.current_position.cmd_argbegin = i
			end_pos = self.current_position.end
			self.context_update(self.current_position.begin)
			new_str = ""
			position = self.current_position.copy()
			if ident == "":
				self.send_error("unrecognized command name '{}'".format(string))
			elif ident in self.commands:
				# todo try
				self.context_update(self.current_position.cmd_begin, "in command {}".format(ident))
				command = self.commands[ident]
				new_str = command(self, arg_string)
				self.context_pop()
			elif ident in self.blocks:
				endblock_b, endblock_e = self.find_matching_endblock(ident, string[self.current_position.end:])
				if endblock_b == -1:
					self.send_error('no matching endblock for block {}'.format(ident))
				self.current_position.endblock_begin = endblock_b + self.current_position.end
				self.current_position.endblock_end = endblock_e + self.current_position.end
				block_content = string[
					self.current_position.end : self.current_position.endblock_begin
				]
				end_pos = self.current_position.endblock_end
				block = self.blocks[ident]

				# block post action don't trickle upwards
				self.context_update(self.current_position.cmd_begin, "in block {}".format(ident))

				new_str = block(self, arg_string, block_content)

				self.context_pop()
			else:
				self.send_error("command or block not recognized")
			self.current_position = position
			self.context_pop()
			string = self.replace_string(
				self.current_position.begin, end_pos, string, new_str, tokens
			)
			self.remove_leading_close_tokens(tokens)
		# end while
		if len(tokens) == 1:
			self.send_error(
				'lonely token, use "{}begin{}" or "{}end{}" to place it'.format(
					self.token_begin, self.token_end, self.token_begin, self.token_end
				)
			)

		# Post actions
		self.context_update(0, "in post actions")
		for action in self.post_actions:
			string = action(self, string)
		self.context_pop()

		self._recursion_depth -= 1
		if empty_context:
			self._context = []
		self.current_position.offset = old_offset

		self.post_actions = post_actions

		return string
