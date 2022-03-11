"""
This is the packages __main__. It defines the command-line argument parser
and when run as main, executes the preprocessor using arguments from sys.argv
"""

import argparse
from os.path import abspath, dirname
from pathlib import Path
from sys import stderr, stdin, stdout
from typing import List, Optional

from .defaults import Preprocessor, define_macro
from .defs import PREPROCESSOR_NAME, PREPROCESSOR_VERSION
from .errors import ErrorMode, WarningMode

parser = argparse.ArgumentParser(prog=PREPROCESSOR_NAME, add_help=False)
parser.add_argument("--begin", "-b", nargs="?", default=None)
parser.add_argument("--end", "-e", nargs="?", default=None)
parser.add_argument("--warnings", "-w", nargs="?", default=None, choices=("hide", "error"))
parser.add_argument("--version", "-v", action="store_true")
parser.add_argument("--output", "-o", nargs="?", type=Path, default=stdout)
parser.add_argument("--help", "-h", nargs="?", const="", default=None)
parser.add_argument("--define", "-d", "-D", nargs="?", action="append", default=[])
parser.add_argument(
	"--include", "-i", "-I", nargs=1, action="append", default=[], type=abspath# type: ignore
)
parser.add_argument("--silent", "-s", nargs=1, default=[], action="append")
parser.add_argument("--recursion-depth", "-r", nargs=1, type=int)
parser.add_argument("input", nargs="?", type=Path, default=stdin)



def process_defines(preproc: Preprocessor, defines: List[str]) -> None:
	"""process command line defines
	defines should be a list of strings like "<ident>" or "<ident>=<value>"
	"""
	for define in defines:
		if isinstance(define, list):
			define = define[0] # argparse creates nested list for some reason
		i = define.find("=")
		if i == -1:
			name = define
			value = ""
		else:
			name = define[:i]
			value = define[i+1:]
		if not name.isidentifier():
			parser.error("argument --define/-d/-D: invalid define name \"{}\"".format(
				name
			))
			exit(1)
		define_macro(preproc, name, [], value)

def process_options(preproc: Preprocessor, arguments: argparse.Namespace) -> None:
	"""process the preprocessor options
	see Preprocessor.get_help("") for a list and description of options"""
	# adding input/output commands
	input_name = str(arguments.input) if isinstance(arguments.input, Path) else "<stdin>"
	command = lambda *args: input_name
	command.doc = "Prints name of input file" # type: ignore
	preproc.commands["input_name"] = command
	output_name = str(arguments.output) if isinstance(arguments.output, Path) else "<stdout>"
	command = lambda *args: output_name
	command.doc = "Prints name of output file" # type: ignore
	preproc.commands["output_name"] = command

	# adding defined commands
	process_defines(preproc, arguments.define)

	# include path
	preproc.include_path = [
		abspath(""), # CWD
		dirname(abspath(input_name)),
		dirname(abspath(output_name)),
	] + arguments.include

	# recursion depth
	if arguments.recursion_depth is not None:
		rec_depth = arguments.recursion_depth[0]
		if rec_depth < -1:
			parser.error("argument --recusion-depth/-r: number must be greater than -1")
			exit(1)
		preproc.max_recursion_depth = rec_depth

	# tokens
	if arguments.begin is not None:
		preproc.token_begin = arguments.begin
	if arguments.end is not None:
		preproc.token_end = arguments.end

	# warning mode
	if arguments.warnings == "hide":
		preproc.warning_mode = WarningMode.HIDE
	elif arguments.warnings == "error":
		preproc.warning_mode = WarningMode.AS_ERROR
	else:
		preproc.warning_mode = WarningMode.PRINT

	# silent warnings
	preproc.silent_warnings.extend([x[0] for x in arguments.silent])

	# version and help
	if arguments.version:
		print("{} version {}".format(PREPROCESSOR_NAME, PREPROCESSOR_VERSION))
		exit(0)
	if arguments.help is not None:
		print(preproc.get_help(arguments.help))
		exit(0)

def preprocessor_main(argv: Optional[List[str]] = None) -> None:
	"""main function for the preprocessor
	handles arguments, reads contents from file
	and write result to output file.
	argv defaults to sys.argv
	"""
	preprocessor = Preprocessor()
	preprocessor.warning_mode = WarningMode.PRINT
	preprocessor.error_mode = ErrorMode.PRINT_AND_EXIT

	if argv is None:
		args = parser.parse_args()
	else:
		args = parser.parse_args(argv)

	if stderr.isatty():
		preprocessor.use_color = True

	process_options(preprocessor, args)

	if isinstance(args.input, Path):
		try:
			input_name = str(args.input)
			with open(args.input, "r") as file:
				contents = file.read()
		except FileNotFoundError:
			parser.error("argument input: file not found \"{}\"".format(args.input))
		except PermissionError:
			parser.error("argument input: permission denied \"{}\"".format(args.input))
	else:
		# read from stdin
		input_name = "<stdin>"
		contents = args.input.read()

	result = preprocessor.process(contents, input_name)

	if isinstance(args.output, Path):
		try:
			with open(args.output, "w") as file:
				file.write(result)
		except FileNotFoundError:
			parser.error("argument -o/--output: no such file or directory \"{}\"".format(args.output))
		except PermissionError:
			parser.error("argument -o/--output: permission denied \"{}\"".format(args.output))
	else:
		# write to stdout
		args.output.write(result)


if __name__ == "__main__":
	preprocessor_main()
