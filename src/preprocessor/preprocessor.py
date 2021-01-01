#!/usr/bin/python3
import re
from sys import stderr
from typing import Dict, Callable, List

from defs import *


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
		return "hello"

	def find_matching_pair(self: "Preprocessor", tokens) -> int:
		"""find the first innermost OPEN CLOSE pair in tokens
		Inputs:
		  tokens - list of tuples containing 4 elements
				tokens[i][3] should be a boolean indicating
				OPEN with True and CLOSE with False
		Returns
      the first index i such that tokens[i][3] == True and tokens[i+1][3] == False
      -1 if no such index exists
		"""
		len_tokens = len(tokens)
		token_index = 0
		while (
			tokens[token_index][3] != TokenMatch.OPEN
			or tokens[token_index + 1][3] != TokenMatch.CLOSE
		):
			token_index += 2
			if token_index + 1 > len_tokens:
				return -1
		return token_index

	def parse(self: "Preprocessor", string: str) -> str:
		self._recursion_depth += 1
		if self._recursion_depth == self.max_recursion_depth:
			self.send_error("Recursion depth exceeded")

		open_tokens  = re.findall(self.token_begin, string, self.re_flags)
		close_tokens = re.findall(self.token_end, string, self.re_flags)
		tokens =  [(x, x.start(), x.end(), TokenMatch.OPEN)  for x in open_tokens]
		tokens += [(x, x.start(), x.end(), TokenMatch.CLOSE) for x in close_tokens]
		# sort in order of appearance - if two tokens appear at same place
		# sort CLOSE first
		tokens.sort(key=lambda x: x[1] + 0.5 * int(x[3]))

		len_tokens = len(tokens)
		while len_tokens > 1:  # needs two tokens to make a pair

			# find innermost (nested pair)
			token_index = self.find_matching_pair(tokens)
			if token_index == -1:
				self.send_error("No matching open/close pair found")

			substring = string[tokens[token_index][2] : tokens[token_index + 1][1]]
			ident = self.get_identifier_name(substring)
			if ident in self.functions:
				del tokens[token_index]
				del tokens[token_index]
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
