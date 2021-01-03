# -*- coding: utf-8 -*-
import argparse
import re

from .defs import REGEX_IDENTIFIER_WRAPPED, ArgumentParserNoExit
from .preprocessor import Preprocessor

# ============================================================
# strip commands
# ============================================================


def pst_strip_empty_lines(p: Preprocessor, string: str) -> str:
	"""post action to remove empty lines (containing whitespace only) from the text"""
	return re.sub(r"\n\s*\n", "\n", string)

def cmd_strip_empty_lines(preprocessor: Preprocessor, s: str) -> str:
	"""the strip_empty_lines command
	queues pst_strip_empty_lines to preprocessor.post_actions"""
	if s.strip() != "":
		preprocessor.send_warning("strip_empty_line takes no arguments")
	preprocessor.post_actions.append(pst_strip_empty_lines)
	return ""

def pst_strip_leading_whitespace(p: Preprocessor, string: str) -> str:
	"""post action to remove leading whitespace (indent) from string"""
	return re.sub("^[ \t]*", "", string, flags = re.MULTILINE)

def cmd_strip_leading_whitespace(preprocessor: Preprocessor, s: str) -> str:
	"""the strip_leading_whitespace command
	queues pst_strip_leading_whitespace to preprocessor.post_actions"""
	if s.strip() != "":
		preprocessor.send_warning("strip_leading_whitespace takes no arguments")
	preprocessor.post_actions.append(pst_strip_leading_whitespace)
	return ""

def pst_strip_trailing_whitespace(p: Preprocessor, string: str) -> str:
	"""post action to remove trailing whitespace (indent) from string"""
	return re.sub("[ \t]*$", "", string, flags = re.MULTILINE)

def cmd_strip_trailing_whitespace(preprocessor: Preprocessor, s: str) -> str:
	"""the strip_trailing_whitespace command
	queues pst_strip_trailing_whitespace to preprocessor.post_actions"""
	if s.strip() != "":
		preprocessor.send_warning("strip_trailing_whitespace takes no arguments")
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
		preprocessor.send_warning("empty_last_line takes no arguments")
	preprocessor.post_actions.append(pst_empty_last_line)
	return ""


# ============================================================
# replace command
# ============================================================


replace_parser = ArgumentParserNoExit(
	prog="replace", add_help=False
)

replace_parser.add_argument("--regex", "-r", action="store_true")
replace_parser.add_argument("--ignore-case", "-i", action="store_true")
replace_parser.add_argument("--whole-word", "-w", action="store_true")
replace_parser.add_argument("--count", "-c", nargs='?', default=0, type=int)
replace_parser.add_argument("pattern")
replace_parser.add_argument("replacement")

def cmd_replace(p: Preprocessor, args: str) -> str:
	"""the replace command
	usage: replace [-r|--regex] [-i|--ignore-case] [-w|--whole-word]
	               [-c|--count <number>] pattern replacement
	"""
	try:
		arguments = replace_parser.parse_args(p.split_args(args))
	except argparse.ArgumentError:
		p.send_error(
			"invalid argument.\n"
			"usage: replace [-r|--regex] [-i|--ignore-case] [-w|--whole-word]"
			"               [-c|--count <number>] pattern replacement")
	flags = re.MULTILINE
	pattern = arguments.pattern
	repl = arguments.replacement
	if arguments.ignore_case:
		flags |= re.IGNORECASE
	if arguments.regex:
		if arguments.whole_word:
			p.send_error("incompatible arguments : --regex and --whole-word")
	else:
		pattern = re.escape(pattern)
		if arguments.whole_word:
			pattern = REGEX_IDENTIFIER_WRAPPED.format(pattern)
			repl = "\\1{}\\3".format(repl)
	count = arguments.count
	if count < 0:
		p.send_error("invalid argument.\nthe replace --count argument must be positive")
	pos = p.current_position.cmd_begin

	def pst_replace(p: Preprocessor, string: str) -> str:
		try:
			return re.sub(pattern, repl, string, count=count, flags = flags)
		except re.error as err:
			p.context_update(pos)
			p.send_error("replace regex error: {}".format(err.msg))
			p.context_pop()
			return ""
	pst_replace.__name__ = "pst_replace_lambda"
	pst_replace.__doc__ = "post action for replace {}".format(args)
	p.post_actions.append(pst_replace)
	return ""
