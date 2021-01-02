#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re
from datetime import datetime

from .defs import process_string
from .preprocessor import Preprocessor

# ============================================================
# def/undef
# ============================================================

def cmd_def(preprocessor: Preprocessor, args_string : str) -> str:
	ident, text, _ = preprocessor.get_identifier_name(args_string)
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
		text = process_string(text[1:-1])

	def defined_command(p: Preprocessor, s: str) -> str:
		if is_macro:
			pass
		return p.parse(text)
	defined_command.__doc__ = """Defined command for {}""".format(ident)
	defined_command.__name__ = """cmd_{}""".format(ident)
	preprocessor.commands[ident] = defined_command
	return ""

def cmd_undef(preprocessor: Preprocessor, args_string: str) -> str:
	"""The undef command, removes commands or blocks
	from preprocessor.commands and preprocessor.blocks
	usage: undef <command-name>"""
	ident = preprocessor.get_identifier_name(args_string)[0]
	if ident == "":
		preprocessor.send_error("invalid identifier")
	if ident in preprocessor.commands:
		del preprocessor.commands[ident]
	elif ident in preprocessor.blocks:
		del preprocessor.commands[ident]
	else:
		preprocessor.send_error("can't undefine \"{}\", it aldready undefined")
	return ""

# ============================================================
# begin/end
# ============================================================

def cmd_begin(preprocessor: Preprocessor, args_string: str) -> str:
	"""The begin command, inserts token_begin
	usage: begin [uint]
	  begin -> token_begin
		begin 0 -> token_begin
		begin <number> -> token_begin begin <number-1> token_end"""
	args_string = args_string.strip()
	level = 0
	if args_string != "":
		if args_string.isnumeric():
			level = int(args_string)
		else:
			preprocessor.send_error("invalid argument: usage begin [uint]")
		if level < 0:
			preprocessor.send_error("invalid argument: usage begin [uint]")
	if level == 0:
		return preprocessor.token_begin_repr
	else:
		return preprocessor.token_begin_repr + "begin " + str(level-1) + preprocessor.token_end_repr

def cmd_end(preprocessor: Preprocessor, args_string: str) -> str:
	"""The end command, inserts token_end
	usage: end [uint]
	  end -> token_end
		end 0 -> token_end
		end <number> -> token_end end <number-1> token_end"""
	args_string = args_string.strip()
	level = 0
	if args_string != "":
		if args_string.isnumeric():
			level = int(args_string)
		else:
			preprocessor.send_error("invalid argument. Usage: end [uint]")
		if level < 0:
			preprocessor.send_error("invalid argument. Usage: end [uint]")
	if level == 0:
		return preprocessor.token_end_repr
	else:
		return preprocessor.token_begin_repr + "end " + str(level-1) + preprocessor.token_end_repr

def cmd_label(preprocessor: Preprocessor, arg_string: str) -> str:
	"""the label command
	usage: label label_name
	  adds the label to preprocessor.labels[label_name]
		which can be used by other commands/blocks
	"""
	lbl = arg_string.strip()
	if lbl == "":
		preprocessor.send_error("empty label name")
	if lbl in preprocessor.labels:
		preprocessor.labels[lbl].append(preprocessor.current_position.begin)
	else:
		preprocessor.labels[lbl] = [preprocessor.current_position.begin]
	return ""

def cmd_date(p: Preprocessor, args: str) -> str:
	"""the date command, prints the current date in YYYY-MM-DD format"""
	args = args.strip()
	if args == "":
		args = "YYYY-MM-DD"
	# we need to use a placeholder to avoid conflits
	# in successive replaces
	replacements = (
		("YYYY", "\0001", "{year:04}"),
		("YY", "\0002", "{year2:02}"),
		("Y", "\0003", "{year}"),
		("MM", "\0004", "{month:02}"),
		("M", "\0005", "{month}"),
		("DD", "\0006", "{day:02}"),
		("D", "\0007", "{day}"),
		("hh", "\0008", "{hour:02}"),
		("h", "\0009", "{hour}"),
		("mm", "\000a", "{minute:02}"),
		("m", "\000b", "{minute}"),
		("ss", "\000c", "{second:02}"),
		("s", "\000d", "{second}"),
	)
	for val, placeholder, _ in replacements:
		args = args.replace(val, placeholder)
	for _, placeholder, repl in replacements:
		args = args.replace(placeholder, repl)
	print(args)
	x = datetime.now()
	return args.format(year = x.year, month = x.month, day = x.day,
		hour = x.hour, minute = x.minute, second = x.second, year2 = x.year % 100
	)

# TODO include, extends,
