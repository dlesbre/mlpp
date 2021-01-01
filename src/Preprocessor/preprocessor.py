#!/usr/bin/python3
# -*- coding: utf-8 -*-
import re
from sys import stderr
from typing import Callable, Dict, List, Optional, Tuple, cast

from .defs import *

TokenList = List[Tuple[int, int, TokenMatch]]
DilatationList = List[Tuple[int, int]]

class Preprocessor:

	# constants
	max_recursion_depth: int = 20
	token_begin: str = re.escape("{% ")
	token_end: str = re.escape(" %}")
	token_endblock: str = re.escape("end")
	token_ident: str = REGEX_IDENTIFIER
	token_ident_end: str = REGEX_IDENTIFIER_END
	re_flags: int = re.MULTILINE
	exit_code: int = 2

	# if False raises an error
	# if True print to stderr and exit
	exit_on_error: bool = True

	# if True, handle warnings as errors
	warning_mode: WarningMode = WarningMode.PRINT

	warn_unmatch_close: bool = False

	# private attributes
	_recursion_depth: int = 0
	_context: List[str] = []

	# functions and blocks
	functions: Dict[str, Callable[["Preprocessor", str], str]] = dict()
	blocks: Dict[str, Callable[["Preprocessor", str, str], str]] = dict()
	post_actions: List[Callable[["Preprocessor", str], str]] = []

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
			print("Error: {}".format(error_msg), file=stderr)
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
			print("Warning: {}".format(warning_msg), file=stderr)
		elif self.warning_mode == WarningMode.RAISE:
			raise Warning(warning_msg)
		elif self.warning_mode == WarningMode.AS_ERROR:
			self.send_error(warning_msg)

	def get_identifier_name(self: "Preprocessor", string: str) -> Tuple[str, str]:
		"""finds the first identifier in string:
		Returns:
			tuple str, str - identifier, rest_of_string
		  returns ("","") if None found"""
		match_opt = re.match(r"\s*({})({}*.)".format(self.token_ident, self.token_ident_end), string)
		if match_opt == None:
			return "", ""
		match = cast(re.Match, match_opt)
		return match.group(1), match.group(2)

	def find_tokens(self: "Preprocessor", string: str) -> TokenList:
		"""Find all tokens (begin/end) in string
		Inputs:
			string: str - the string to search for tokens
		Returns:
			tokens: List[int, TokenMatch] - list of (position, OPEN/CLOSE)
				sorted by position (CLOSE comes first if equal)
		"""
		open_tokens  = re.finditer(self.token_begin, string, self.re_flags)
		close_tokens = re.finditer(self.token_end, string, self.re_flags)
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
			token_index += 2
			if token_index + 1 > len_tokens:
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
			self.token_begin, self.token_endblock, block_name, self.token_end
		)
		startblock_regex = r"{}\s*{}(?:{}|{})".format(
			self.token_begin, block_name, self.token_end, self.token_ident_end
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
		start: int, end: int, string: str, replacement: str,
		tokens: TokenList, dilatations: DilatationList
	) -> str:
		"""replaces string[start:end] with replacement
		also add offset to token requiring them
		Returns:
			str = string[:start] + replacement + string[end:]
		Effect:
			removes all tokens occuring between start and end from tokens
			corrects start and end of further tokens by the length change
			adds the length change to self._dilatations
		"""
		test_range = range(start, end)
		i = 0
		dilat = len(replacement) - (end - start)
		while i < len(tokens):
			if tokens[i][0] in test_range or tokens[i][1] in test_range:
				del tokens[i]
			else:
				if tokens[i][0] > end:
					tokens[i] = (
						tokens[i][0] + dilat,
						tokens[i][1] + dilat,
						tokens[i][2],
					)
				i += 1

		dilatations.append((start, dilat))
		return string[:start] + replacement + string[end:]

	def remove_leading_close_tokens(self: "Preprocessor", tokens: TokenList) -> None:
		"""removes leading close tokens from tokens
		if self.warn_unmatch_close is true, issues a warning"""
		while tokens and tokens[0][2] == TokenMatch.CLOSE:
			del tokens[0]
			if self.warn_unmatch_close:
				self.send_warning("Unmatch close token")

	def step_in_recursion(self: "Preprocessor") -> str:
		pass

	def parse(self: "Preprocessor", string: str) -> str:
		self._recursion_depth += 1
		if self._recursion_depth == self.max_recursion_depth:
			self.send_error("Recursion depth exceeded")

		tokens: TokenList = self.find_tokens(string)
		dilatations: DilatationList = []

		while len(tokens) > 1:  # needs two tokens to make a pair

			# find innermost (nested pair)
			token_index = self.find_matching_pair(tokens)
			if token_index == -1:
				self.send_error("No matching open/close pair found")

			substring = string[
				tokens[token_index][1] : tokens[token_index + 1][0]
			]
			ident, arg_string = self.get_identifier_name(substring)
			start_pos = tokens[token_index][0]
			end_pos = tokens[token_index + 1][1]
			new_str = ""
			if ident == "":
				self.send_error("Unrecognized command name")
			elif ident in self.functions:
				# todo context
				command = self.functions[ident]
				new_str = command(self, arg_string)
			elif ident in self.blocks:
				endblock, end_pos = self.find_matching_endblock(ident, string[start_pos:])
				if endblock == -1 and end_pos == -1:
					self.send_error('No matching endblock for block {}'.format(ident))
				endblock += start_pos
				end_pos += start_pos
				block_content = string[end_pos:endblock]
				block = self.blocks[ident]
				new_str = block(self, arg_string, block_content)
			else:
				self.send_error("Command or block not recognized")

			string = self.replace_string(
				start_pos, end_pos, string, new_str, tokens, dilatations
			)
			self.remove_leading_close_tokens(tokens)

		if len(tokens) == 1:
			self.send_error(
				'lonely token, use "{}begin{}" or "{}end{}" to place it'.format(
					self.token_begin, self.token_end, self.token_begin, self.token_end
				)
			)

		# Post actions
		for action in self.post_actions:
			string = action(self, string)

		return string
