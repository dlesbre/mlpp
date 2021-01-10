import argparse
from sys import stdin, stdout

from .defaults import FileDescriptor, Preprocessor
from .defs import PREPROCESSOR_NAME, PREPROCESSOR_VERSION, WarningMode

parser = argparse.ArgumentParser(prog=PREPROCESSOR_NAME, add_help=False)
parser.add_argument("--begin", "-b", nargs="?", default=None)
parser.add_argument("--end", "-e", nargs="?", default=None)
parser.add_argument("--warnings", "-w", nargs="?", default=None, choices=("hide", "error"))
parser.add_argument("--version", "-v", action="store_true")
parser.add_argument("--output", "-o", nargs="?", type=argparse.FileType("w"), default=stdout)
parser.add_argument("input", nargs="?", type=argparse.FileType("r"), default=stdin)

preproc = Preprocessor()

if __name__ == "__main__":
	arguments = parser.parse_args()
	if arguments.version:
		print("{} version {}".format(PREPROCESSOR_NAME, PREPROCESSOR_VERSION))
		exit(0)
	if arguments.begin is not None:
		preproc.token_begin = arguments.begin
	if arguments.end is not None:
		preproc.token_end = arguments.end
	if arguments.warnings == "hide":
		preproc.warning_mode = WarningMode.HIDE
	elif arguments.warnings == "error":
		preproc.warning_mode = WarningMode.AS_ERROR
	else:
		preproc.warning_mode = WarningMode.PRINT

	contents = arguments.input.read()

	preproc.context.new(FileDescriptor(arguments.input.name, contents), 0)
	result = preproc.parse(contents)
	preproc.context.pop()

	arguments.output.write(result)
