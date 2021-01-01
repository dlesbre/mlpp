#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
from datetime import datetime

from .preprocessor import Preprocessor


def define(preprocessor: Preprocessor, args_string : str) -> str:
	ident, text = preprocessor.get_identifier_name(args_string)
	if ident == "":
		preprocessor.send_error("invalid identifier")

	# removed trailing\leading whitespace
	text = text.strip()
	is_macro = False
	args = []
	#
	if text and text[0] == "(":
		is_macro = True
		end = text.find(")")
		if end == -1:
			preprocessor.send_error('no matching closing ")" in macro definition\nEnclose in quotes to have a paranthese as first character')
		args = text[1:end].split(",")
		for i in range(len(args)):
			args[i] = args[i].strip()
		text = text[end+1:].strip()

	# if its a string - use escapes and remove external quotes
	if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
		text = text[1:-1].encode().decode("unicode-escape")

	def defined_command(p: Preprocessor, s: str) -> str:
		if is_macro:
			pass
		return p.parse(text)
	defined_command.__doc__ = """Defined command for {}""".format(ident)
	preprocessor.commands[ident] = defined_command
	return ""

def undef(preprocessor: Preprocessor, args_string: str) -> str:
	"""The undef command, removes commands or blocks
	from preprocessor.commands and preprocessor.blocks
	usage: undef <command-name>"""
	ident, _ = preprocessor.get_identifier_name(args_string)
	if ident == "":
		preprocessor.send_error("invalid identifier")
	if ident in preprocessor.commands:
		del preprocessor.commands[ident]
	elif ident in preprocessor.blocks:
		del preprocessor.commands[ident]
	else:
		preprocessor.send_error("can't undefine \"{}\", it aldready undefined")
	return ""

def date(p: Preprocessor, s: str) -> str:
	x = datetime.now()
	return "{:04}-{:02}-{:02}".format(x.year, x.month, x.day)

Preprocessor.commands["def"] = define
Preprocessor.commands["undef"] = undef
Preprocessor.commands["date"] = date
