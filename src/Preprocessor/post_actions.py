#!/usr/bin/python3
# -*- coding: utf-8 -*-

import re

from .preprocessor import Preprocessor

# ============================================================
# post parse commands
# ============================================================

# TODO replace

def pst_strip_empty_lines(p: Preprocessor, string: str) -> str:
	"""post action to remove empty lines (containing whitespace only) from the text"""
	return re.sub(r"\n\s*\n", "\n", string)

def cmd_strip_empty_lines(preprocessor: Preprocessor, s: str) -> str:
	"""the strip_empty_lines command
	queues pst_strip_empty_lines to preprocessor.post_actions"""
	if s.strip() != "":
		preprocessor.send_error("empty_last_line takes no arguments")
	preprocessor.post_actions.append(pst_strip_empty_lines)
	return ""

def pst_strip_leading_whitespace(p: Preprocessor, string: str) -> str:
	"""post action to remove leading whitespace (indent) from string"""
	return re.sub("^[ \t]*", "", string, flags = re.MULTILINE)

def cmd_strip_leading_whitespace(preprocessor: Preprocessor, s: str) -> str:
	"""the strip_leading_whitespace command
	queues pst_strip_leading_whitespace to preprocessor.post_actions"""
	if s.strip() != "":
		preprocessor.send_error("empty_last_line takes no arguments")
	preprocessor.post_actions.append(pst_strip_leading_whitespace)
	return ""

def pst_strip_trailing_whitespace(p: Preprocessor, string: str) -> str:
	"""post action to remove trailing whitespace (indent) from string"""
	return re.sub("[ \t]*$", "", string, flags = re.MULTILINE)

def cmd_strip_trailing_whitespace(preprocessor: Preprocessor, s: str) -> str:
	"""the strip_trailing_whitespace command
	queues pst_strip_trailing_whitespace to preprocessor.post_actions"""
	if s.strip() != "":
		preprocessor.send_error("empty_last_line takes no arguments")
	preprocessor.post_actions.append(pst_strip_trailing_whitespace)
	return ""

def pst_empty_last_line(p: Preprocessor, string: str) -> str:
	"""post action to ensures file ends with an empty line if
	it is not empty"""
	if string and string[-1] != "\n":
		string += "\n"
	else:
		ii = len(string) - 2
		while ii >= 0 and string[ii] == "\n":
			ii -= 1
		string = string[:ii+2]
	return string

def cmd_empty_last_line(preprocessor: Preprocessor, s: str) -> str:
	"""the empty_last_line command
	queues pst_empty_last_line to preprocessor.post_actions"""
	if s.strip() != "":
		preprocessor.send_error("empty_last_line takes no arguments")
	preprocessor.post_actions.append(pst_empty_last_line)
	return ""

def cmd_replace(preprocessor: Preprocessor, s: str) -> str:
	"""the replace command
	usage: replace [-r|--regex] [-i|--ignore-case] [-w|--whole-word] "pattern" "replacement"
	"""
	pattern = ""
	repl = ""
	def pst_replace(p: Preprocessor, string: str) -> str:
		return re.sub(pattern, repl, string) # TODO
	preprocessor.post_actions.append(pst_replace)
	return ""

# TODO blocks verbatim repeat, labelblock, for, if, atlabel
