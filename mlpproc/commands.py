"""
Definitions of default preprocessor commands
"""
import argparse
import re
from datetime import datetime
from os.path import abspath, dirname, isfile, join
from typing import List

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
		preprocessor.send_error("manual-error", "raised by error command.")
	else:
		preprocessor.send_error("manual-error", "raised by error command.\n{}".format(args))
	return ""

cmd_error.doc = ( # type: ignore
	"""
	Raises an error.
	Use with if block to raise errors if conditions are not met.

	Usage: error [message]
	""")

def cmd_warning(preprocessor: Preprocessor, args: str) -> str:
	"""the warning command - raises a warning
	usage: warning [msg]"""
	args = args.strip()
	if args == "":
		preprocessor.send_warning("manual-warning", "raised by warning command.")
	else:
		preprocessor.send_warning("manual-warning", "raised by warning command.\n{}".format(args))
	return ""

cmd_warning.doc = ( # type: ignore
	"""
	Raises a warning.
	Use with if block to raise warnings if conditions are not met.

	Usage: warning [message]
	""")

def cmd_version(preprocessor: Preprocessor, args: str) -> str:
	"""the version command - prints the preprocessor version"""
	if args.strip() != "":
		preprocessor.send_warning("extra-arguments", "the version command takes no arguments")
	return PREPROCESSOR_VERSION

cmd_version.doc = ( # type: ignore
	"""
	Prints the preprocessor version.
	""")

def cmd_filename(preprocessor: Preprocessor, args: str) -> str:
	"""the file command - prints the current file name"""
	if args.strip() != "":
		preprocessor.send_warning("extra-arguments", "the file command takes no arguments")
	return preprocessor.context.top.file.filename

cmd_filename.doc = ( # type: ignore
	"""
	Prints the name of the current file being parsed.
	""")

def cmd_line(preprocessor: Preprocessor, args: str) -> str:
	"""the line command - prints the current line number"""
	if args.strip() != "":
		preprocessor.send_warning("extra-arguments", "the line command takes no arguments")
	context = preprocessor.context.top
	pos = context.true_position(preprocessor.current_position.begin)
	return str(context.file.line_number(pos)[0])

cmd_line.doc = ( # type: ignore
	"""
	Prints the current line number.
	This is the line number of the command in the input file, the line
	in the output file may differ due to insertions/deletions.
	""")

# ============================================================
# def/undef
# ============================================================


macro_parser = ArgumentParserNoExit(prog="macro", add_help=False)
macro_parser.add_argument('vars', nargs='*') # arbitrary number of arguments

def rreplace(string, old, new, occurrence = 1):
	"""replace <occurrence> number of old by new in string
	starting with the right"""
	split = string.rsplit(old, occurrence)
	return new.join(split)

def define_macro(preprocessor: Preprocessor, name: str, args: List[str], text: str) -> None:
	"""Defines a macro.
	Inputs:
	- preprocessor - the object to which the macro is added
	- name: str - the name of the new macro
	- args: List[str] - List or arguments name
	- text: str - the text the command prints. Occurrences of args will
	  be replaced by the corresponding value during the call.
	  will only replace occurrence that aren't part of a larger word
	"""
	# replace arg occurences with placeholder
	for i, arg in enumerate(args):
		text = re.sub(
			REGEX_IDENTIFIER_WRAPPED.format(re.escape(arg)), # pattern
			"\\1{}\\3".format("\000(arg {})\000".format(i)), # placeholder
			text,
			flags = re.MULTILINE
		)
	# define the command
	def cmd(pre: Preprocessor, cmd_args: List[str], text: str = text, ident: str = name) -> str:
		"""a defined macro command"""
		for i, arg in enumerate(cmd_args):
			pattern = re.escape("\000(arg {})\000".format(i))
			text = re.sub(pattern, arg, text, flags=re.MULTILINE)

		pre.context.update(
			pre.current_position.cmd_argbegin,
			'in expansion of defined command {}'.format(ident)
		)
		parsed = pre.parse(text)
		pre.context.pop()
		return parsed

	cmd.doc = "{} {}".format(name, " ".join(args)) # type: ignore
	# place it in command_vars
	if "def" not in preprocessor.command_vars:
		preprocessor.command_vars["def"] = dict()
	preprocessor.command_vars["def"]["{}:{}".format(name, len(args))] = cmd

	overloads = []
	usages = []
	for key, val in preprocessor.command_vars["def"].items():
		if key.startswith(name+":"):
			overloads.append(int(key[key.find(":") + 1]))
			usages.append(val.doc)
	usage = "usage: " + "\n       ".join(usages)
	overload_nb = rreplace(", ".join(str(x) for x in sorted(overloads)), ", ", " or ")

	# overwrite defined command
	def defined_cmd(pre: Preprocessor, args_string: str) -> str:
		"""This is the actual command, parses arguments
		and calls the correct overload"""
		split = pre.split_args(args_string)
		try:
			arguments = macro_parser.parse_args(split)
		except argparse.ArgumentError:
			pre.send_error("invalid-argument",
				"invalid argument for macro.\n{}".format(usage)
			)
		if len(arguments.vars) not in overloads:
			pre.send_error("invalid-argument",(
				"invalid number of arguments for macro.\nexpected {} got {}.\n"
				"{}").format(overload_nb, len(arguments.vars), usage)
			)
		return pre.command_vars["def"]["{}:{}".format(name, len(arguments.vars))](
			pre, arguments.vars
		)

	defined_cmd.__doc__ = "Defined command for {} (expects {} arguments)\n{}".format(
		name, overload_nb, usage
	)
	defined_cmd.doc = defined_cmd.__doc__ # type: ignore
	defined_cmd.__name__ = """def_cmd_{}""".format(name)

	preprocessor.commands[name] = defined_cmd

def cmd_def(preprocessor: Preprocessor, args_string : str) -> str:
	"""the define command - inspired by the C preprocessor's define
	usage:
		def <ident> <replacement> -> defines ident with replacement
			(strips leading/trailing space)
		def <ident> " replacement with leading/trailing space  "
		def <ident>(<ident1>, <ident2>) replacement
			defines a macro"""
	ident, text, _ = get_identifier_name(args_string)
	if ident == "":
		preprocessor.send_error("invalid-identifier",
			"invalid identifier.\ndef needs a valid identifier, got \"{}\"".format(args_string)
		)

	# removed trailing\leading whitespace
	text = text.strip()
	args = []

	if text and text[0] == "(":
		end = text.find(")")
		if end == -1:
			preprocessor.send_error("unmatched-open-parenthese",
				'no matching closing ")" in macro definition\n'
				'Enclose in quotes to have a paranthese as first character'
			)
		args = text[1:end].split(",")
		len_args = len(args)
		for i in range(len_args):
			args[i] = args[i].strip()
			if not args[i].isidentifier():
				preprocessor.send_error("invalid-identifier",
					'in def {}: invalid macro parameter name "{}"'.format(ident, args[i])
				)
		for arg in args:
			if args.count(arg) > 1:
				preprocessor.send_error("invalid-identifier",
					'in def {}: multiple macro parameters with same name "{}"'.format(ident, arg)
				)
		text = text[end+1:].strip()

	# if its a string - use escapes and remove external quotes
	if len(text) >= 2 and text[0] in preprocessor.string_delimiters and text[-1] == text[0]:
		text = process_string(text[1:-1])

	define_macro(preprocessor, ident, args, text)
	return ""

cmd_def.doc = ( # type: ignore
	"""
	Defines a new command or macro.

	Usage:
	 def foo               -> defines empty foo command (prints nothing)
	 def foo   some text   -> {% foo %} prints "some text"
	                          (strips trailing/leading space)
	 def foo " some text " -> {% foo %} prints " some text "
	 def foo(arg1, arg2) text with arg1 and arg2
	    -> {% foo bar "hi there" %} prints "text with bar and hi there"

	def overwrites old commands and blocks irreversibly.
	All defs are global, including those comming from subblocks and included files.

	defs can use nesting and recursive calls using command like call, begin and end.

	  {% def name john %}

	  // name is evaluated before def
	  {% def rec1 {% name %} %}

	  // call evaluated before def, prints {% name %}
	  // which will be evaluated when define is called
	  {% def rec2 {% call name %} %}

	  // 1rst call evaluated in define, prints {% call name %}
	  // which will be evaluated when define is called
	  {% def rec3 {% call call name %} %}

	  {% def name alice %}
	  {% rec1 %} -> prints john
	  {% rec2 %} -> prints alice
	  {% rec3 %} -> prints {% name %}

	defs can be overloaded on the number of arguments

	  {% def sum(a,b) a+b %}
	  {% def sum(a)   {% sum a 0 %} %}
	  {% sum 5 10 %} -> prints 5+10
	  {% sum 5 %}    -> prints 5+0
	""")

def cmd_undef(preprocessor: Preprocessor, args_string: str) -> str:
	"""The undef command, removes commands or blocks
	from preprocessor.commands and preprocessor.blocks
	usage: undef <command-name>"""
	ident = get_identifier_name(args_string)[0]
	if ident == "":
		preprocessor.send_error("invalid-identifier",
			"invalid identifier in undef: \"{}\"".format(args_string)
		)
	undefined = False
	if ident in preprocessor.commands:
		del preprocessor.commands[ident]
		undefined = True
	if ident in preprocessor.blocks:
		del preprocessor.commands[ident]
		undefined = True
	if not undefined:
		preprocessor.send_warning("aldready-undefined",
			"can't undef \"{}\", identifier is aldready undefined.".format(ident)
		)
	if "def" in preprocessor.command_vars:
		del_keys = []
		for key in preprocessor.command_vars:
			if key.startswith(ident+"<"):
				del_keys.append(key)
		for key in del_keys:
			del preprocessor.command_vars["def"][key]
	return ""

cmd_undef.doc = ( # type: ignore
	"""
	Undefines a command or block.
	This is irreversible and can undefine built-in commands and blocks.

	Usage: undef name
	""")

def cmd_deflist(preprocessor: Preprocessor, args_string: str) -> str:
	"""The deflist command, used to define lists
	usage: deflist <list_name> space separated list "element with spaces"
		list_name must be a valid identifier

	Defines a new command list_name such that
		list_name prints the lists
		list_name n prints the n-th element (n must be a between -length+1,length+1)
	"""
	ident, text, _ = get_identifier_name(args_string)
	if ident == "":
		preprocessor.send_error("invalid-identifier",
			"invalid identifier.\ndeflist needs a valid identifier, got \"{}\"".format(args_string)
		)
	defined_list = preprocessor.split_args(text)
	def defined_command(pre: Preprocessor, args: str) -> str:
		args = args.strip()
		if is_integer(args):
			index = to_integer(args)
			list_len = len(defined_list)
			if index <= - list_len or index >= list_len:
				pre.send_error("invalid-index",
					"invalid index.\nDefined list {} has length {}, can't access element {}.".format(
						ident, list_len, index
					)
				)
			return defined_list[index]
		if args == "":
			return text
		pre.send_error("invalid-argument",
			"invalid argument for defined list \"{}\".\nusage {} [<number>]".format(
				args, ident)
		)
		return ""
	preprocessor.commands[ident] = defined_command
	return ""

cmd_deflist.doc = ( # type: ignore
	"""
	Defines a new command.

	Usage: deflist list_name space separated list " element with spaces "

	Defines list_name such that:
		list_name          prints the lists
		list_name <number> prints the n-th element
		                   (number must be a between -length+1 and length+1)

	Can be used in combination with the for block to iterate multiple lists in a loop.
	""")

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
			preprocessor.send_error("invalid-argument","invalid argument: usage begin [uint]")
		if level < 0:
			preprocessor.send_error("invalid-argument","invalid argument: usage begin [uint]")
	if level == 0:
		return preprocessor.token_begin
	return preprocessor.token_begin + " begin " + str(level-1) + " " + preprocessor.token_end

cmd_begin.doc = ( # type: ignore
	"""
	Prints the current begin token (default "{%")

	Usage: begin [<number>]
	The optional number is used for recursion calls
	  begin     -> "{%"
	  begin 0   -> "{%"
	  begin <n> -> "{% begin <n-1> %}"
	""")

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
			preprocessor.send_error("invalid-argument","invalid argument. Usage: end [uint]")
		if level < 0:
			preprocessor.send_error("invalid-argument","invalid argument. Usage: end [uint]")
	if level == 0:
		return preprocessor.token_end
	else:
		return preprocessor.token_begin + " end " + str(level-1) + " " + preprocessor.token_end

cmd_end.doc = ( # type: ignore
	"""
	Prints the current end token (default "%}")

	Usage: end [<number>]
	The optional number is used for recursion calls
	  end     -> "%}"
	  end 0   -> "%}"
	  end <n> -> "{% end <n-1> %}"
	""")

def cmd_call(preprocessor: Preprocessor, args_string: str) -> str:
	"""The call command: used to print begin and end tokens
	usage: {% call foo bar ... %} -> {% foo bar ... %}"""
	args_string = args_string.strip()
	if (len(args_string) >= 2 and
			args_string[0] in preprocessor.string_delimiters and
			args_string[-1] == args_string[0]):
		args_string = args_string[1:-1]
	return preprocessor.token_begin + " " + args_string + " " + preprocessor.token_end

cmd_call.doc = ( # type: ignore
	"""
	Prints a call to its arguments.

	Ex: "{% call my_command my_args %}" -> "{% my_command my_args %}"
	Useful in defs to use recursive calls.
	For recursion you can stack calls:
	"{% call call ... %}" -> "{% call ... %}"
	""")

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
		preprocessor.send_error("invalid-label", "empty label name")
	preprocessor.labels.add_label(lbl, preprocessor.current_position.relative_begin)
	return ""

cmd_label.doc = ( # type: ignore
	"""
	Adds a label at the current position

	Usage: label <label_name>
	Where label_name must be a valid identifier.

	Can be used in combination with the atlabel block
	to place text at all occurrences of a label.
	""")

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
		pre.send_error("invalid-argument",
			"invalid argument.\nusage: paste [-v|--verbatim] [<clipboard_name>]"
		)
	clipboard = arguments.clipboard
	if (
		("clipboard" not in pre.command_vars)
		or (clipboard not in pre.command_vars["clipboard"])
	):
		pre.send_warning("paste-undefined", "trying to paste undefined clipboard")
		return ""
	context, text = pre.command_vars["clipboard"][clipboard]
	if not arguments.verbatim:
		pre.context.new(context.file, context.position, context.description)
		text = pre.parse(text)
		pre.context.pop()
	return text

cmd_paste.doc = ( # type: ignore
	"""
	Pastes the contents of a clipboard (defined in a cut block)

	Usage: paste [-v|--verbatim] [clipboard]
	  if --verbatim is set, paste the text as is, without rendering it
	  clipboard is a string identifying the clipboard (default "").
	  it must match a previous cut block's clipboard argument
	""")

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

cmd_date.doc = ( # type: ignore
	"""
	Prints the current date.

	Usage: date [format=YYYY-MM-DD]
	  format specifies year with YYYY or YY, month with MM or M,
	  day with DD or D, hour with hh or h, minutes with mm or m
	  seconds with ss or s
	""")


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
		preprocessor.send_error("invalid-argument",
			"invalid argument.\nusage: include [-v|--verbatim] file_path"
		)
	filepath = arguments.file_path
	if not isfile(filepath):
		for include in preprocessor.include_path:
			if isfile(join(include, filepath)):
				filepath = join(include, filepath)
				break
		else:
			preprocessor.send_error("file-error",'file not found "{}"'.format(arguments.file_path))
	try:
		with open(filepath, "r") as file:
			contents = file.read()
	except FileNotFoundError:
		preprocessor.send_error("file-error",'file not found "{}"'.format(arguments.file_path))
	except PermissionError:
		preprocessor.send_error("file-error",'can\'t open file "{}", permission denied'.format(arguments.file_path))
	except Exception:
		preprocessor.send_error("file-error",'can\'t open file "{}"'.format(arguments.file_path))
	if not arguments.verbatim:
		begin = preprocessor.token_begin
		end = preprocessor.token_end
		if arguments.begin is not None:
			preprocessor.token_begin = arguments.begin
		if arguments.end is not None:
			preprocessor.token_end = arguments.end
		preprocessor.include_path.append(dirname(abspath(filepath)))
		preprocessor.context.new(FileDescriptor(arguments.file_path, contents), 0, "in included file")
		contents = preprocessor.parse(contents)
		preprocessor.context.pop()
		preprocessor.token_begin = begin
		preprocessor.token_end = end
	return contents

cmd_include.doc = ( # type: ignore
	"""
	Includes the content of another file.

	Usage: include [--options] path
	  path can be absolute or relative to
	  any path in include_path: [current_working_dir, input_file_dir, output_file_dir]
	  paths can be added to include_path with the --include/-i/-I preprocessor option

	Options:
	  -b --begin <string> specify the begin token ("{%")
	                      defaults to the same as current file
	  -e --end   <string> specify the end token ("%}")
	                      defaults to the same as current file
	  -v --verbatim       when present, includes files as is, without parsing.
	""")
