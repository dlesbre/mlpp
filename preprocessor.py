#!/usr/bin/python3
import re

REGEX_IDENTIFIER = "[_a-zA-Z][_a-zA-Z0-9]*"
REGEX_STRING = '""|".*?[^\\\\]"'

class Position():
	file = "stdin"
	line = 0
	char = 0
	def __init__(file, line, char):
		self.file = file
		self.line = line
		self.char = char

class CommandError(Exception):
	def __init__(self, position, msg):
		self.file = file
		self.line = line
		self.msg = msg

def define(processor, args_string):
	match = re.match(REGEX_IDENTIFIER, args_string)
	if match is None:
		raise CommandError(processor.current_pos, "Define has no valid command name")
	identifier = match.group()

	return ""

class Preproccesor():

	# constants
	max_recursion_depth = 20
	token_begin    = re.escape("{% ")
	token_end      = re.escape(" %}")
	token_endblock = re.escape("end")
	re_flags       = re.MULTILINE

	# private attributes
	_recursion_depth = 0
	_context = []

	# functions and blocks
	functions = dict()
	blocks = dict()
	post_actions = []

	def send_error(self, error):
		pass

	def send_warning(self, error):
		pass

	def get_command_name(self, string):
		pass

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
		while tokens[token_index][3] != OPEN or tokens[token_index+1][3] != CLOSE:
			token_index += 2
			if token_index + 1 > len_tokens:
				return -1
		return token_index

	def parse(self, string):
		self._recursion_level += 1
		if self._recursion_depth == max_recursion_depth:
			pass

		open_tokens = re.findall(self.token_begin, input_string, self.re_flags)
		if open_tokens == []:
			pass

		OPEN  = True
		CLOSE = False

		close_tokens = re.findall(self.token_end, input_string[match_begin.start():], self.re_flags)
		tokens =  [(x, x.start(), x.end(), OPEN)  for x in open_tokens]
		tokens += [(x, x.start(), x.end(), CLOSE) for x in close_tokens]
		tokens.sort(key = lambda x: x[1]) # sort in order of appearance

		len_tokens = len(tokens)
		while len_tokens > 1: # needs two tokens to make a pair

			# find innermost (nested pair)
			token_index = self.find_matching_pair(tokens)
			if token_index == -1:
				self.send_error("No matching open/close pair found")
			substring = input_string[tokens[token_index][2]:tokens[token_index[1]]]
			command = self.find_command(substring)
			if command != None:
				pass
			else:
				block = self.find_block(substring)
				if block == None:
					self.send_error("Command or block not recognized"
				)

			del tokens[token_index]
			del tokens[token_index]
			len_tokens -= 2
			# todo - shift indexes

		if len_tokens == 1:
			self.send_error('lonely token, use "{} begin {}" or "{} end {}" to place it'.format(
				self.token_begin, self.token_end, self.token_begin, self.token_end))



