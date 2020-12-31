#!/usr/bin/python3
import re
from enum import Enum

REGEX_IDENTIFIER = "[_a-zA-Z][_a-zA-Z0-9]*"
REGEX_STRING = '""|".*?[^\\\\]"'


class Position:
	file = "stdin"
	line = 0
	char = 0

	def __init__(self, file, line, char):
		self.file = file
		self.line = line
		self.char = char


class CommandError(Exception):
	def __init__(self, position, msg):
		self.pos = position
		self.msg = msg


def define(processor, args_string):
	match = re.match(REGEX_IDENTIFIER, args_string)
	if match is None:
		raise CommandError(processor.current_pos, "Define has no valid command name")
	identifier = match.group()

	return ""


class WarningMode(Enum):
	HIDE = 1
	PRINT = 2
	RAISE = 3
	AS_ERROR = 4


class TokenMatch(Enum):
	OPEN = 1
	CLOSE = 2


class Preprocessor:

	# constants
	max_recursion_depth = 20
	token_begin = re.escape("{% ")
	token_end = re.escape(" %}")
	token_endblock = re.escape("end")
	re_flags = re.MULTILINE

	# if False raises an error
	# if True print to stderr and exit
	exit_on_error = True

	# if True, handle warnings as errors
	warning_mode = WarningMode.PRINT

	# private attributes
	_recursion_depth = 0
	_context = []

	# functions and blocks
	functions = dict()
	blocks = dict()
	post_actions = []

	def send_error(self, error_msg):
		"""Handles errors
		Inputs:
      self - Preprocessor object
      error_msg - string : an error message
		Effect:
      if self.exit_on_error print message and exit
      else raise an Exception
		"""
		if self.exit_on_error:
			print("Error: {}".format(error_msg))
		else:
			raise Exception(error_msg)

	def send_warning(self, warning_msg):
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
			print("Warning: {}".format(warning_msg))
		elif self.warning_mode == WarningMode.RAISE:
			raise Warning(warning_msg)
		elif self.warning_mode == WarningMode.AS_ERROR:
			self.send_error(warning_msg)

	def get_identifier_name(self, string):
		return 0

	def find_matching_pair(self, tokens):
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

	def parse(self, string):
		self._recursion_depth += 1
		if self._recursion_depth == self.max_recursion_depth:
			self.send_error("Recursion depth exceeded")

		open_tokens = re.findall(self.token_begin, string, self.re_flags)
		close_tokens = re.findall(self.token_end, string, self.re_flags)
		tokens =  [(x, x.start(), x.end(), TokenMatch.OPEN)  for x in open_tokens]
		tokens += [(x, x.start(), x.end(), TokenMatch.CLOSE) for x in close_tokens]
		# sort in order of appearance - if two tokens appear at same place
		# sort CLOSE first
		tokens.sort(key=lambda x: x[1] + 0.5 * x[3])

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
