"""
Definitions of default preprocessor final actions
and the commands that trigger them
"""
import argparse
import re

from .defs import REGEX_IDENTIFIER_WRAPPED, ArgumentParserNoExit
from .preprocessor import Preprocessor

# ============================================================
# strip commands
# ============================================================


def fnl_strip_empty_lines(_: Preprocessor, string: str) -> str:
	"""final action to remove empty lines (containing whitespace only) from the text"""
	return re.sub(r"\n\s*\n", "\n", string)

def cmd_strip_empty_lines(preprocessor: Preprocessor, args: str) -> str:
	"""the strip_empty_lines command
	queues fnl_strip_empty_lines to preprocessor final actions"""
	if args.strip() != "":
		preprocessor.send_warning("strip_empty_line takes no arguments")
	preprocessor.add_finalaction(fnl_strip_empty_lines)
	return ""

def fnl_strip_leading_whitespace(_: Preprocessor, string: str) -> str:
	"""final action to remove leading whitespace (indent) from string"""
	return re.sub("^[ \t]*", "", string, flags = re.MULTILINE)

def cmd_strip_leading_whitespace(preprocessor: Preprocessor, args: str) -> str:
	"""the strip_leading_whitespace command
	queues fnl_strip_leading_whitespace to preprocessor final actions"""
	if args.strip() != "":
		preprocessor.send_warning("strip_leading_whitespace takes no arguments")
	preprocessor.add_finalaction(fnl_strip_leading_whitespace)
	return ""

def fnl_strip_trailing_whitespace(_: Preprocessor, string: str) -> str:
	"""final action to remove trailing whitespace (indent) from string"""
	return re.sub("[ \t]*$", "", string, flags = re.MULTILINE)

def cmd_strip_trailing_whitespace(preprocessor: Preprocessor, args: str) -> str:
	"""the strip_trailing_whitespace command
	queues fnl_strip_trailing_whitespace to preprocessor final actions"""
	if args.strip() != "":
		preprocessor.send_warning("strip_trailing_whitespace takes no arguments")
	preprocessor.add_finalaction(fnl_strip_trailing_whitespace)
	return ""

def fnl_fix_last_line(_: Preprocessor, string: str) -> str:
	"""final action to ensures file ends with an empty line if
	it is not empty"""
	if string and string[-1] != "\n":
		string += "\n"
	else:
		ii = len(string) - 2
		while ii >= 0 and string[ii] == "\n":
			ii -= 1
		string = string[:ii+2]
	return string

def cmd_fix_last_line(preprocessor: Preprocessor, args: str) -> str:
	"""the fix_last_line command
	queues fnl_fix_last_line to preprocessor final actions"""
	if args.strip() != "":
		preprocessor.send_warning("fix_last_line takes no arguments")
	preprocessor.add_finalaction(fnl_fix_last_line)
	return ""

def fnl_fix_first_line(_: Preprocessor, string: str) -> str:
	"""final action to ensures file starts with a non-empty
	non-whitespace line (if it is not empty)"""
	while string != "":
		pos = string.find("\n")
		if pos == -1:
			if string.isspace():
				return ""
			return string
		elif string[:pos+1].isspace():
			string = string[pos+1:]
		else:
			break
	return string

def cmd_fix_first_line(preprocessor: Preprocessor, args: str) -> str:
	"""the fix_first_line command
	queues fnl_fix_first_line to preprocessor final actions"""
	if args.strip() != "":
		preprocessor.send_warning("fix_last_line takes no arguments")
	preprocessor.add_finalaction(fnl_fix_first_line)
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
replace_parser.add_argument("text", nargs="?", default=None, action="store")

def cmd_replace(preprocessor: Preprocessor, args: str) -> str:
	"""the replace command
	usage: replace [-r|--regex] [-i|--ignore-case] [-w|--whole-word]
	               [-c|--count <number>] pattern replacement [text]
		if text is present, replace in text and print
		else queue final action to replace in current block
	"""
	split = preprocessor.split_args(args)
	try:
		arguments = replace_parser.parse_args(split)
	except argparse.ArgumentError:
		preprocessor.send_error(
			"invalid argument.\n"
			"usage: replace [-r|--regex] [-i|--ignore-case] [-w|--whole-word]\n"
			"               [-c|--count <number>] pattern replacement [text]")
	flags = re.MULTILINE
	pattern = arguments.pattern
	repl = arguments.replacement
	if arguments.ignore_case:
		flags |= re.IGNORECASE
	if arguments.regex:
		if arguments.whole_word:
			preprocessor.send_error("incompatible arguments : --regex and --whole-word")
	else:
		pattern = re.escape(pattern)
		if arguments.whole_word:
			pattern = REGEX_IDENTIFIER_WRAPPED.format(pattern)
			repl = "\\1{}\\3".format(repl)
	count = arguments.count
	if count < 0:
		preprocessor.send_error("invalid argument.\nthe replace --count argument must be positive")
	pos = preprocessor.current_position.cmd_begin
	if arguments.text is not None:
		try:
			return re.sub(pattern, repl, arguments.text, count=count, flags = flags)
		except re.error as err:
			preprocessor.send_error("replace regex error: {}".format(err.msg))
			return ""
	# no text, queue post action
	def fnl_replace(preprocessor: Preprocessor, string: str) -> str:
		try:
			return re.sub(pattern, repl, string, count=count, flags = flags)
		except re.error as err:
			preprocessor.context.update(pos)
			preprocessor.send_error("replace regex error: {}".format(err.msg))
			preprocessor.context.pop()
			return ""
	fnl_replace.__name__ = "fnl_replace_lambda"
	fnl_replace.__doc__ = "final action for replace {}".format(args)
	preprocessor.add_finalaction(fnl_replace)
	return ""



# ============================================================
# upper/lower/capitalize commands
# ============================================================

def fnl_upper(_: Preprocessor, string: str) -> str:
	"""Final action for upper, transforms
	text in string to UPPER CASE"""
	return string.upper()

def cmd_upper(preprocessor: Preprocessor, args: str) -> str:
	"""The upper command, switches text to UPPER CASE
	usage: upper [text]
		with text -> returns TEXT (ignores trailing/leading spaces)
		without   -> queues final action to transform all text in current block
			to UPPER CASE"""
	args = args.strip()
	if args:
		if len(args) >= 2 and args[0] == '"' and args[-1] == '"':
			args = args[0:-1]
		return args.upper()
	preprocessor.add_finalaction(fnl_upper)
	return ""

def fnl_lower(_: Preprocessor, string: str) -> str:
	"""Final action for upper, transforms
	text in string to lower case"""
	return string.lower()

def cmd_lower(preprocessor: Preprocessor, args: str) -> str:
	"""The lower command, switches text to lower case
	usage: lower [text]
		with TEXT -> returns text (ignores trailing/leading spaces)
		without   -> queues final action to transform all text in current block
			to lower case"""
	args = args.strip()
	if args:
		if len(args) >= 2 and args[0] == '"' and args[-1] == '"':
			args = args[0:-1]
		return args.lower()
	preprocessor.add_finalaction(fnl_lower)
	return ""

def fnl_capitalize(_: Preprocessor, string: str) -> str:
	"""Final action for upper, transforms
	text in string to Capitalized Case"""
	return string.capitalize()

def cmd_capitalize(preprocessor: Preprocessor, args: str) -> str:
	"""The capitalize command, switches text to lower case
	usage: capitalize [text]
		with text -> returns Text (ignores trailing/leading spaces)
		without   -> queues final action to transform all text in current block
			to Capitalized Case"""
	args = args.strip()
	if args:
		if len(args) >= 2 and args[0] == '"' and args[-1] == '"':
			args = args[0:-1]
		return args.capitalize()
	preprocessor.add_finalaction(fnl_capitalize)
	return ""
