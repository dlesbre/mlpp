#!/usr/bin/python3
# -*- coding: utf-8 -*-

from datetime import datetime

from .preprocessor import Preprocessor


def define(preprocessor: Preprocessor, args_string : str) -> str:
	ident, text = preprocessor.get_identifier_name(args_string)
	if ident == "":
		preprocessor.send_error("def does not start with a valid identifier")

	# removed trailing\leading whitespace
	text = text.strip()


	if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
		text = text[1:-1].encode().decode("unicode-escape")


	def defined_command(p: Preprocessor, s: str) -> str:
		return p.parse(text)
	defined_command.__doc__ = """Defined command for {}""".format(ident)
	preprocessor.commands[ident] = defined_command
	return ""

def date(p: Preprocessor, s: str) -> str:
	x = datetime.now()
	return "{:04}-{:02}-{:02}".format(x.year, x.month, x.day)

Preprocessor.commands["def"] = define
Preprocessor.commands["date"] = date
