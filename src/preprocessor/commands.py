# -*- coding: utf-8 -*-
import argparse
import re
from datetime import datetime

from .context import FileDescriptor
from .defs import *
from .preprocessor import Preprocessor

# ============================================================
# simple commands
# ============================================================

def cmd_error(preprocessor: Preprocessor, args: str) -> str:
	"""the error command - raises an error
	usage: error [msg]"""
	args = args.strip()
	if args == "":
		preprocessor.send_error("raised by error command.")
	else:
		preprocessor.send_error("raised by error command.\n{}".format(args))
	return ""

def cmd_warning(preprocessor: Preprocessor, args: str) -> str:
	"""the warning command - raises a warning
	usage: warning [msg]"""
	args = args.strip()
	if args == "":
		preprocessor.send_warning("raised by warning command.")
	else:
		preprocessor.send_warning("raised by warning command.\n{}".format(args))
	return ""

def cmd_version(preprocessor: Preprocessor, args: str) -> str:
	"""the version command - prints the preprocessor version"""
	if args.strip() != "":
		preprocessor.send_warning("the version command takes no arguments")
	return PREPROCESSOR_VERSION

def cmd_file(preprocessor: Preprocessor, args: str) -> str:
	"""the file command - prints the current file name"""
	if args.strip() != "":
		preprocessor.send_warning("the file command takes no arguments")
	return preprocessor.context.top.file.filename

def cmd_line(preprocessor: Preprocessor, args: str) -> str:
	"""the line command - prints the current line number"""
	if args.strip() != "":
		preprocessor.send_warning("the line command takes no arguments")
	context = preprocessor.context.top
	pos = context.true_position(preprocessor.current_position.begin)
	return str(context.file.line_number(pos)[0])

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
		preprocessor.send_error(
			"invalid identifier.\ndef needs a valid identifier, got \"{}\"".format(args_string)
		)

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

	def defined_command(pre: Preprocessor, args_string: str) -> str:
		string = text
		if is_macro:
			split = pre.split_args(args_string)
			try:
				arguments = macro_parser.parse_args(split)
			except argparse.ArgumentError:
				pre.send_error("invalid argument for macro.\nusage: {} {}".format(ident, " ".join(args)))
			if len(arguments.vars) != len(args):
				pre.send_error((
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

		pre.context.update(
			pre.current_position.cmd_argbegin,
			'in expansion of defined command {}'.format(ident)
		)
		parsed = pre.parse(string)
		pre.context.pop()
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

def cmd_deflist(preprocessor: Preprocessor, args_string: str) -> str:
	"""The deflist command, used to define lists
	usage: deflist <list_name> space separated list "element with spaces"
		list_name must be a valid identifier

	Defines a new command list_name such that
		list_name prints the lists
		list_name n prints the n-th element (n must be a between -lenght+1,length+1)
	"""
	ident, text, _ = get_identifier_name(args_string)
	if ident == "":
		preprocessor.send_error(
			"invalid identifier.\ndeflist needs a valid identifier, got \"{}\"".format(args_string)
		)
	defined_list = preprocessor.split_args(text)
	def defined_command(pre: Preprocessor, args: str) -> str:
		args = args.strip()
		if is_integer(args):
			index = to_integer(args)
			list_len = len(defined_list)
			if index <= - list_len or index >= list_len:
				pre.send_error(
					"invalid index.\nDefined list {} has length {}, can't access element {}.".format(
						ident, list_len, index
					)
				)
			return defined_list[index]
		if args == "":
			return text
		pre.send_error(
			"invalid argument for defined list \"{}\".\nusage {} [<number>]".format(
				args, ident)
		)
		return ""
	preprocessor.commands[ident] = defined_command
	return ""


# ============================================================
# begin/end/call
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

def cmd_call(preprocessor: Preprocessor, args_string: str) -> str:
	"""The call command: used to print begin and end tokens
	usage: {% call foo bar ... %} -> {% foo bar ... %}"""
	return preprocessor.token_begin + args_string + preprocessor.token_end


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
	preprocessor.labels.add_label(lbl, preprocessor.current_position.relative_begin)
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
	context, text = pre.command_vars["clipboard"][clipboard]
	if not arguments.verbatim:
		pre.context.new(context.file, context.position, context.description)
		text = pre.parse(text)
		pre.context.pop()
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
	date = datetime.now()
	return args.format(year = date.year, month = date.month, day = date.day,
		hour = date.hour, minute = date.minute, second = date.second,
		year2 = date.year % 100
	)


# ============================================================
# include
# ============================================================


include_parser = ArgumentParserNoExit(
	prog="include", description="places the contents of the file at file_path",
  add_help=False
)

include_parser.add_argument("--verbatim", "-v", action="store_true")
include_parser.add_argument("--begin", "-b", nargs="?", default=None)
include_parser.add_argument("--end", "-e", nargs="?", default=None)
include_parser.add_argument("file_path")

def cmd_include(preprocessor: Preprocessor, args: str) -> str:
	"""the include command
	usage: include [-v|--verbatim] [-b|--begin <str>] [-e|--end <str>] file_path
	  places the contents of the file at file_path
		--verbatim specifies that the file should not be parsed, it is parsed by default
		--begin and --end can be used to set different preprocessor tokens
			for the file being included"""
	split = preprocessor.split_args(args)
	try:
		arguments = include_parser.parse_args(split)
	except argparse.ArgumentError:
		preprocessor.send_error("invalid argument.\nusage: include [-v|--verbatim] file_path")
	try:
		with open(arguments.file_path, "r") as file:
			contents = file.read()
	except FileNotFoundError:
		preprocessor.send_error('file not found "{}"'.format(arguments.file_path))
	except PermissionError:
		preprocessor.send_error('can\'t open file "{}", permission denied'.format(arguments.file_path))
	except Exception:
		preprocessor.send_error('can\'t open file "{}"'.format(arguments.file_path))
	if not arguments.verbatim:
		begin = preprocessor.token_begin
		end = preprocessor.token_end
		if arguments.begin is not None:
			preprocessor.token_begin = arguments.begin
		if arguments.end is not None:
			preprocessor.token_end = arguments.end
		preprocessor.context.new(FileDescriptor(arguments.file_path, contents), 0, "in included file")
		contents = preprocessor.parse(contents)
		preprocessor.context.pop()
		preprocessor.token_begin = begin
		preprocessor.token_end = end
	return contents
