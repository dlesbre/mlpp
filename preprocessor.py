#!/usr/bin/python3
import re

TOKEN_BEGIN = re.escape("{%")
TOKEN_END   = re.escape("%}")

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

class PreFunction():

	def __init__(self, function, parse_args = True, recursive = True)
		self.function = function
		self.parse_args = parse_args
		self.recursive = recursive

def define(processor, args_string):
	match = re.match(REGEX_IDENTIFIER, args_string)
	if match is None:
		raise CommandError(processor.current_pos, "Define has no valid command name")
	identifier = match.group()

define = PreFunction(define, parse_args = False, recursive = True)

class Preproccesor():

	functions = dict()
	blocks = dict()

	def parse(self, string):
		re.escape