#!/usr/bin/python3
import re
from sys import stderr
from typing import Dict, Callable, List, Tuple, cast

from .defs import *

TokenList = List[Tuple[int, TokenMatch]]

class Preprocessor:

	# constants
	max_recursion_depth: int = 20
	token_begin: str = re.escape("{% ")
	token_end: str = re.escape(" %}")
	token_endblock: str = re.escape("end")
	re_flags: int = re.MULTILINE
	exit_code: int = 2

	# if False raises an error
	# if True print to stderr and exit
	exit_on_error: bool = True

	# if True, handle warnings as errors
	warning_mode: WarningMode = WarningMode.PRINT

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

	def get_identifier_name(self: "Preprocessor", string: str) -> str:
		"""find and returns the first identifier in string
		return "" if None found"""
		match_opt = re.match(r"\s*({})".format(REGEX_IDENTIFIER), string)
		if match_opt == None:
			return ""
		match = cast(re.Match, match_opt)
		return match.group(1)

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
		tokens =  [(x.start(), TokenMatch.OPEN)  for x in open_tokens]
		tokens += [(x.start(), TokenMatch.CLOSE) for x in close_tokens]
		# sort in order of appearance - if two tokens appear at same place
		# sort CLOSE first
		tokens.sort(key=lambda x: x[0] + 0.5 * int(x[1]))
		return tokens

	def find_matching_pair(self: "Preprocessor", tokens: TokenList) -> int:
		"""find the first innermost OPEN CLOSE pair in tokens
		Inputs:
		  tokens - list of tuples containing 4 elements
				tokens[i][3] should be a boolean indicating
				OPEN with True and CLOSE with False
				Assumed to be at least 2 elements long
		Returns
      the first index i such that tokens[i][3] == True and tokens[i+1][3] == False
      -1 if no such index exists
		"""
		len_tokens = len(tokens)
		token_index = 0
		while (
			tokens[token_index][1] != TokenMatch.OPEN
			or tokens[token_index + 1][1] != TokenMatch.CLOSE
		):
			token_index += 2
			if token_index + 1 > len_tokens:
				return -1
		return token_index

	def parse(self: "Preprocessor", string: str) -> str:
		self._recursion_depth += 1
		if self._recursion_depth == self.max_recursion_depth:
			self.send_error("Recursion depth exceeded")

		self._tokens = self.find_tokens(string)

		len_tokens = len(self._tokens)
		while len_tokens > 1:  # needs two tokens to make a pair

			# find innermost (nested pair)
			token_index = self.find_matching_pair(self._tokens)
			if token_index == -1:
				self.send_error("No matching open/close pair found")

			substring = string[
				self._tokens[token_index][0] + len(self.token_begin) :\
				self._tokens[token_index + 1][0]
			]
			ident = self.get_identifier_name(substring)
			if ident == "":
				self.send_error("Unrecognized command name")
			elif ident in self.functions:
				del self._tokens[token_index]
				del self._tokens[token_index]
				len_tokens -= 2
				# todo - shift indexes
			elif ident in self.blocks:
				pass
			else:
				self.send_error("Command or block not recognized")

		if len_tokens == 1:
			self.send_error(
				'lonely token, use "{} begin {}" or "{} end {}" to place it'.format(
					self.token_begin, self.token_end, self.token_begin, self.token_end
				)
			)
		return ""
