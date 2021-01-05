# -*- coding: utf-8 -*-
import argparse
import re
from datetime import datetime

from .defs import *
from .preprocessor import Preprocessor

# ============================================================
# simple commands
# ============================================================

def cmd_error(p: Preprocessor, args: str) -> str:
	"""the error command - raises an error
	usage: error [msg]"""
	args = args.strip()
	if args == "":
		p.send_error("raised by error command")
	else:
		p.send_error("raised by error command: {}".format(args))
	return ""

def cmd_warning(p: Preprocessor, args: str) -> str:
	"""the warning command - raises a warning
	usage: warning [msg]"""
	args = args.strip()
	if args == "":
		p.send_warning("raised by warning command")
	else:
		p.send_warning("raised by warning command: {}".format(args))
	return ""

def cmd_version(p: Preprocessor, args: str) -> str:
	"""the version command - prints the preprocessor version"""
	if args.strip() != "":
		p.send_warning("the version command takes no arguments")
	return PREPROCESSOR_VERSION

def cmd_file(p: Preprocessor, args: str) -> str:
	"""the file command - prints the current file name"""
	if args.strip() != "":
		p.send_warning("the file command takes no arguments")
	return p.get_context().file

def cmd_line(p: Preprocessor, args: str) -> str:
	"""the line command - prints the current line number"""
	if args.strip() != "":
		p.send_warning("the line command takes no arguments")
	return str(p.get_context().line_number(p.current_position.begin)[0])

# ============================================================
# def/undef
# ============================================================


macro_parser = ArgumentParserNoExit(prog="macro", add_help=False)
macro_parser.add_argument('vars', nargs='*') # arbitrary number of arguments

def cmd_def(preprocessor: Preprocessor, args_string : str) -> str:
	"""the define command - inspired by the C preprocessor's define
	usage:
		def <ident> <replacement> -> defines ident with replacement
			(strips leading/trailing space)
		def <ident> " replacement with leading/trailin space  "
		def <ident>(<ident1>, <ident2>) replacement
			defines a macro"""
	ident, text, _ = get_identifier_name(args_string)
	if ident == "":
		preprocessor.send_error("invalid identifier")

	# removed trailing\leading whitespace
	text = text.strip()
	is_macro = False
	args = []

	if text and text[0] == "(":
		is_macro = True
		end = text.find(")")
		if end == -1:
			preprocessor.send_error(
				'no matching closing ")" in macro definition\n'
				'Enclose in quotes to have a paranthese as first character'
			)
		args = text[1:end].split(",")
		for i in range(len(args)):
			args[i] = args[i].strip()
			if not args[i].isidentifier():
				preprocessor.send_error('in def {}: invalid macro parameter name "{}"'.format(ident, args[i]))
		for arg in args:
			if args.count(arg) > 1:
				preprocessor.send_error(
					'in def {}: multiple macro parameters with same name "{}"'.format(ident, arg)
				)
		text = text[end+1:].strip()

	# if its a string - use escapes and remove external quotes
	if len(text) >= 2 and text[0] == '"' and text[-1] == '"':
		text = process_string(text[1:-1])

	def defined_command(p: Preprocessor, args_string: str) -> str:
		string = text
		if is_macro:
			split = p.split_args(args_string)
			try:
				arguments = macro_parser.parse_args(split)
			except argparse.ArgumentError:
				p.send_error("invalid argument for macro.\nusage: {} {}".format(ident, " ".join(args)))
			if len(arguments.vars) != len(args):
				p.send_error((
					"invalid number of arguments for macro (expected {} got {}).\n"
					"usage: {} {}").format(
						len(args), len(arguments.vars), ident, " ".join(args)
				))
			# first subsitution : placeholder to avoid conflits
			# with multiple replaces
			for i, arg in enumerate(args):
				pattern = REGEX_IDENTIFIER_WRAPPED.format(re.escape(arg))
				placeholder = "\000{}".format(i)
				repl = "\\1{}\\3".format(placeholder)
				string = re.sub(pattern, repl, string, flags=re.MULTILINE)
			for i in range(len(args)):
				pattern = re.escape("\000{}".format(i))
				repl = arguments.vars[i]
				string = re.sub(pattern, repl, string, flags=re.MULTILINE)

		p.context_update(
			p.current_position.cmd_argbegin,
			'in expansion of defined command {}'.format(ident)
		)
		parsed = p.parse(string)
		p.context_pop()
		return parsed
	defined_command.__doc__ = """Defined command for {}""".format(ident)
	defined_command.__name__ = """def_cmd_{}""".format(ident)
	preprocessor.commands[ident] = defined_command
	return ""

def cmd_undef(preprocessor: Preprocessor, args_string: str) -> str:
	"""The undef command, removes commands or blocks
	from preprocessor.commands and preprocessor.blocks
	usage: undef <command-name>"""
	ident = get_identifier_name(args_string)[0]
	if ident == "":
		preprocessor.send_error("invalid identifier")
	if ident in preprocessor.commands:
		del preprocessor.commands[ident]
	if ident in preprocessor.blocks:
		del preprocessor.commands[ident]
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
		return preprocessor.token_begin
	else:
		return preprocessor.token_begin + "begin " + str(level-1) + preprocessor.token_end

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
		return preprocessor.token_end
	else:
		return preprocessor.token_begin + "end " + str(level-1) + preprocessor.token_end


# ============================================================
# label/paste
# ============================================================


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


paste_parser = ArgumentParserNoExit(prog="cut", add_help=False)
paste_parser.add_argument("--verbatim", "-v", action="store_true")
paste_parser.add_argument("clipboard", nargs="?", default="")

def cmd_paste(pre: Preprocessor, args: str) -> str:
	"""the paste command
	usage: paste [-v|--verbatim] [<clipboard_name>]"""
	split = pre.split_args(args)
	try:
		arguments = paste_parser.parse_args(split)
	except argparse.ArgumentError:
		pre.send_error("invalid argument.\nusage: paste [-v|--verbatim] [<clipboard_name>]")
	clipboard = arguments.clipboard
	if (
		("clipboard" not in pre.command_vars)
		or (clipboard not in pre.command_vars["clipboard"])
	):
		pre.send_warning("trying to paste undefined clipboard")
		return ""
	context, pos, text = pre.command_vars["clipboard"][clipboard]
	if not arguments.verbatim:
		pre.context_new(context, pos)
		text = pre.parse(text)
		pre.context_pop()
	return text



def cmd_date(_: Preprocessor, args: str) -> str:
	"""the date command, prints the current date.
	usage: date [format=YYYY-MM-DD]
	  format specifies year with YYYY or YY, month with MM or M,
		day with DD or D, hour with hh or h, minutes with mm or m
		seconds with ss or s"""
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
	for val, placeholder, _ignore in replacements:
		args = args.replace(val, placeholder)
	for _ignore, placeholder, repl in replacements:
		args = args.replace(placeholder, repl)
	x = datetime.now()
	return args.format(year = x.year, month = x.month, day = x.day,
		hour = x.hour, minute = x.minute, second = x.second, year2 = x.year % 100
	)


# ============================================================
# include/extends
# ============================================================


include_parser = ArgumentParserNoExit(
	prog="include", description="places the contents of the file at file_path",
  add_help=False
)

include_parser.add_argument("--verbatim", "-v", action="store_true")
include_parser.add_argument("file_path")

def cmd_include(p: Preprocessor, args: str) -> str:
	"""the include command
	usage: include [-v|--verbatim] file_path
	  places the contents of the file at file_path
		parse them by default, doesn't parse when verbatim is set"""
	split = p.split_args(args)
	try:
		arguments = include_parser.parse_args(split)
	except argparse.ArgumentError:
		p.send_error("invalid argument.\nusage: include [-v|--verbatim] file_path")
	try:
		with open(arguments.file_path, "r") as file:
			contents = file.read()
	except FileNotFoundError:
		p.send_error('file not found "{}"'.format(arguments.file_path))
	except PermissionError:
		p.send_error('can\'t open file "{}", permission denied'.format(arguments.file_path))
	except Exception:
		p.send_error('can\'t open file "{}"'.format(arguments.file_path))
	if not arguments.verbatim:
		p.context_new(Context(arguments.file_path, contents, "in included file"), 0)
		contents = p.parse(contents)
		p.context_pop()
	return contents
