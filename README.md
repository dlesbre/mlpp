# Preprocessor

Simple program to preprocess text files. It is inspired by the C preprocessor and should work with any language.

## Contents

1. [Installation](https://github.com/Lesbre/preprocessor#installation)
2. [Preprocessor syntax](https://github.com/Lesbre/preprocessor#preprocessor-syntax)
3. [Command line usage](https://github.com/Lesbre/preprocessor#command-line-usage)
4. [Python usage](https://github.com/Lesbre/preprocessor#python-usage)
5. [Command and block reference](https://github.com/Lesbre/preprocessor#command-and-block-reference)
6. [Defining custom commands and blocks](https://github.com/Lesbre/preprocessor#defining-custom-commands-and-blocks)

## Installation

1. Clone or download this repository
2. Run `python3 setup.py install` in the repository folder

	You can install it globaly or in a virtual environment. You may have to run as `sudo` when installing globaly.

3. You're done ! You can now call the preprocessor from a command line with `pproc` or `python3 -m preproc` (see [command line usage](https://github.com/Lesbre/preprocessor#command-line-usage) for arguments). You can also import it in python3 with `import preproc`
4. You can uninstall with `pip uninstall preproc`

## Preprocessor syntax

### Basic syntax

The preprocessor instructions are wrapped between "{% " and " %}" (note the space). These tokens can be changed if they conflict with the syntax of the file's langage.

Preprocessor instructions are split in three categories :

- **commands**: `{% command [args] %}`

	Commands print text where they are placed. For instance `{% date %}` prints the current date.
	Some special commands print no text but perform actions. `{% def name my_name %}` prints nothing but defines a new command `{% name %}` which prints `my_name`.

- **blocks**: `{% block_name [args] %} ... some text ... {% endblock_name %}`

	Blocks work very similarily to commands: they wrap around some text and alter it in some way. For instance the `{% verbatim %}` block prints all text in itself verbatim, without rendering any of the commands.

- **final actions**: some actions can be queued by special commands. They occur once every command and block in the current block has been rendered and affect the whole current block. For instance `{% replace foo bar %}` will replace all instances of "foo" with "bar" in the current block (including occurences before the command is called) but not occurences in higher blocks:

		some text... foo here is not replaced
		{% begin block %}
			foo here is replaced
			{% replace foo bar %}
			foo here is replaced
			{% begin block %}
				foo here is also replaced
			{% endblock %}
			{% command foo as argument isn't replaced %}
			{% command that prints foo %} will be replaced
		{% endblock %}

For a list of command run `pproc -h commands` or see the [command and block reference](https://github.com/Lesbre/preprocessor#command-and-block-reference).

### Nesting and resolution order

Commands can be nested within one another : `{% foo {% bar %} %}`. The most innermost command is called first. So here `{% bar %}` is called, then `{% foo bar_output %}` is called. You can even do `{% {% foo %} %}` which will call `{% foo %}` first, then call `{% foo_output %}`. Note that this will fail if `foo_output` isn't a valid command, just like the previous command will fail is `bar_output` isn't a valid argument for `foo`.

Nesting can also be used for block arguments, but *it can NOT be used for block names and endblock*. This will likely fail block resolution and result in matching the wrong endblock or no endblock.

---

## Command line usage

The preprocessor can be called from the command line with:

	pproc [--flags] [input_file]
	python3 -m preproc [--flags] [input_file]

The default input file is `stdin`. Command line options are:

- `-o --output <file>` specifies a file to write output to. Default is stdout
- `-b --begin <string>` change the begin token (default is `"{% "`)
- `-e --end <string>` change the end token (default is `" %}"`)
- `-r --recursion_depth <number>` set the max recursion depth (default {rec}). Use -1 for no maximum recursion (dangerous)
- `-d -D --define <name>[=<value>]` defines a simple command with name `<name>` which prints `<value>` (nothing if no value). Can be used multiple times on command line
- `-i -I --include <path>` Adds paths to the INCLUDE_PATH. default INCLUDE_PATH is `[".", dir(input_file), dir(output_file)]`. Can be used multiple times on command line
- `w --warnings <hide|error>` choose whether to hide warnings or have them raise an error. default is display.
- `s --silent <warning_name>` silence a specific warning (ex: `"extra-arguments"`)
- `v --version` show version and exit
- `h --help` show this help and exit
- `h --help commands` show a list of commands and blocks and exit
- `h --help <cmd_name>` show help for a specific command of block

## Python usage

The package can be imported in python 3 with `import preproc`. This imports a `Preprocessor` class with all default commands included (see [list](https://github.com/Lesbre/preprocessor#command-and-block-reference)). The simplest way to use the preprocessor is then:

```Python
import preproc

preprocessor = preproc.Preprocessor()

preprocessor.context.new(preproc.FileDescriptor(filename, file_contents), 0)
parsed_contents = preprocessor.parse(file_contents)
preprocessor.context.pop()
```

The two context lines are optionnal but they help with error tracebacks. The first one tells the preprocessor the filename and the position of line break to indicate errors, the other just cleans up afterwards.

You can configure the preprocessor directly via it's public attributes:
- `max_recursion_depth: int` (default 20) - raises an error past this depth
- `token_begin: str` and `token_end: str` (default "{% " and " %}") - tokens wrapping preprocessor calls in the document. They should not be equal or be a simple double quote `"` or paranthese `(` or `)`.
- `token_endblock: str` (default "end") - specifies what form the endblock command takes with the regex `<token_begin>s*<token_endblock><block_name>s*<token_end>`
- `safe_calls: bool` (default True) - if True, catches exceptions raised by command or blocks
- `error_mode: preproc.ErrorMode` (default RAISE), how errors are handled:
	- PRINT_AND_EXIT -> print to stderr and exit
	- PRINT_AND_RAISE -> print to stderr and raise exception
	- RAISE -> raise exception
- `warning_mode: preproc.WarningMode` (default RAISE)
	- HIDE -> do nothing
	- PRINT -> print to stderr
	- RAISE -> raise python warning
	- AS_ERROR -> passes to self.send_error()
- `use_color: bool` (default False) if True, uses ansi color when priting errors



---

## Command and block reference

Here follows a list of predefined commands and blocks. An up to date list can be found by running `pproc -h commands` and detailed descriptions obtained by running `pproc -h <command_name>`.

### Commands

- `{% date [format] %}` prints the current date and time. The default format is "YYYY-MM-DD". In the format string Y is replace by year, M by month, D by day, h by hour, m by minute and s by second. The number of letters (between 1-4) indicates leading zeros, except for Y. YY indicates to use only the last two digits of the year.
- `{% begin <number = 0> %}` - prints the command begin token ("{% " by default). If number is not 0, prints `{% begin <number - 1> %}` for recursion purposes.
- `{% end <number = 0> %}` - prints the command end token (" %}" by default). If number is not 0, prints `{% end <number - 1> %}` for recursion purposes.
- `{% def <identifier> ... %}` - defines a new command:

	- `{% def foo    some text  %}` defines `{% foo %}` which prints `some text` (strips leading/trailing spaces)
	- `{% def foo  "  some "text "  %}` defines `{% foo %}` which prints `  some "text `. Notice that to define a string you only need to start and end with double quotes.
	- `{% def foo(arg1, arg2) "  bar arg1+more_text_arg2" %}` defines `{% foo arg1 arg2 %}` which prints `  bar <arg1_contents>+more_text_arg2`. Argument names must be valid identifiers. Arguments are only replaced if they aren't part of a larger identifier.

	Def overwrites old commands and blocks irreversibly.


	Defs are recursive and can use nesting:

	- `{% def foo {% date %} %}` defines `{% foo %}` which prints the current date.
	- `{% def foo {% begin %}date{% end %} %}` defines `{% foo %}` which prints the current date
	- `{% def foo {% begin 1 %}date{% end 1 %} %}` defines `{% foo %}` which prints `{% date %}`

	Note that in the first example, date is evaluated before def is called and in the second it is evaluated when foo is called:

		{% def name john %}
		{% def rec1 {% foo %}
		{% def rec2 {% begin %}foo{% end %} %}
		{% def name alice %}
		{% rec1 %} -> prints john
		{% rec2 %} -> prints alice

	There is no notion of local defs. All def are global, including those comming from subblocks and included files

- `{% undef <identifier> %}` - undefines commands and blocks named identifier. You can undefine anything, including builtin commands and blocks.
- `{% label <label> %}` - prints no text and sets a label at current position
- `{% include [-v|--verbatim] path %}` - inserts the content of the new file. parses them unless *verbatim* is set.
- `{% error [msg] %}` - sends an error
- `{% warning [msg] %}` - sends a warning
- `{% version %}` - prints the preprocessor's version
- `{% file %}` - prints the current file name
- `{% line %}` - prints the line number of the command in the original file. It can differ in the render dus to commands adding/removing line breaks

These commands print nothing and trigger final actions

- `{% strip_empty_lines %}` - removes all empty lines (containing only whitespace) from current block
- `{% strip_trailing_whitespace %}` - removes all trailing whitespace (space, tabs,...) from the current block
- `{% strip_leading_whitespace %}` - removes leading whitespace (indent) from the current block
- `{% empty_last_line %}` - ensure the current block ends with a single empty (unless it is empty)
- `{% replace [-r|--regex] [-i|--ignore-case] [-w|--whole-word] [-c|--count <number>] "pattern" "replacement" %}`
	replaces all occurences of pattern with replacement in the current block.

	If the regex flag is present, pattern is a regex, replacement can contain `\1`, `\2` to place the groups captured by pattern

	If the whole-word flag is present, only replace occurrences which aren't part of a larger identifier (no letter/underscore before, no letter/underscore/number after).

	The count argument specifies how many occurrences of pattern to replace, from the start. Defaults to 0, replace all occurrences.

### Blocks

- `{% block %}...{% endblock %}` - basic block, used to restrict post actions scope
- `{% verbatim %}...{% endverbatim %}` - copies its contents without parsing them. Stops at first `{% endverbatim %}` not matching a `{% verbatim %}`
- `{% void %}...{% endvoid %}` - run all commands/blocks inside it but prints nothing. Can be used for comments of many definitions without adding linebreaks.
- `{% repeat <number>0> %}...{% endrepeat %}` - renders its contents once and copies it *number* times.
- `{% atlabel <label> %}...{% endatlabel %}` - renders its contents but doesn't print them. As a post action, places a copy of the render at each occurence of *label*.

---

## Defining commands, blocks and final actions

This package is designed to simply add new commands and blocks:

- **commands**: they are function with signature:
	```Python
	def command_func(p: Preprocessor, args: str) -> str
	```

	The first argument is the preprocessor object, the second is the args string entered after the command. For example when calling `{% command_name some args %}` args will contain `" some args"` including leading/trailing spaces.

	The return value is the string to be inserted instead of the command call.

	Command are stored in the preprocessor's `command` dict. They can be added with:

	```Python
	# adds the command to all new Preprocessor objects
	Preprocessor.commands["command_name"] = command_function
	# adds the command to a specific Preprocessor object
	my_preproc_obj.commands["command_name"] = command_function
	```

- **blocks**: they are functions with signature:
	```Python
	def block_func(p: Preprocessor, args: str, block_contents: str) -> str
	```

	`args` is the blocks argument, just like in commands, and `block_contents` is everything between `{% block args %}` and `{% endblock %}`.

	They return a string that replaces the whole block `{% block ... %}...{% endblock %}`

	Blocks are stored in the preprocessor's `blocks` dict. They can be added with:

	```Python
	Preprocessor.blocks["block_name"] = block_func
	```

- **final actions**: they have the same signature as commands:
	```Python
	def final_action_function(p: Preprocessor, text: str) -> str
	```

	Here the `text` arg is the whole text (with all commands rendered).

	The action returns the transformed text.

	Actions are added via methods:

	```Python
	# adds a post action to the whole class
	Preprocessor.static_add_finalaction(post_action_function, [RunActionAt=CurrentLevel])
	# adds a post action to a specific object
	preprocessor_obj.add_finalaction(post_action_function, [RunActionAt=CurrentLevel])
	```

	Adding block actions with commands to run in the current block is pretty simple:

	```Python
	def my_post_action(p: Preprocessor, args: str) -> str:
		# not added to Preprocessor.post_actions
		...

	def my_post_action_command(p: Preprocessor, args: str) -> str:
		# will run in the current block and it's sublocks only
		p.add_finalaction.append(my_post_action)
		return ""

	Preprocessor.commands["run_my_post_action"] = my_post_action_command
	```

### Useful functions

Some useful functions and attribute that are usefull when defining commands or blocks

- `Preprocessor.split_args(self, args: str) -> List[str]` - use split a command or block arguments like the command line would.
	You can then parse them with `argparse`. However, `argparse` exits on parsing errors, so the module provide
	```Python
	class ArgumentParserNoExit(argparse.ArgumentParser):
	```
	which raises `argparse.ArgumentError` instead of exiting, allowing errors to be caught and passed to the preprocessor error handling system.
- `Preprocessor.send_error(self, name: str, msg: str)` - sends an error (and exits). Errors should be only fatal problems. Non-fatal problems should be warnings.
- `Preprocessor.send_warning(self, name: str, msg: str)` - sends a warning.
- `Preprocessor.current_position: Position` - variable containing all position info.
- `Preprocessor.parse(self, string: str) -> str` - processed the string commands and blocks and returns the parsed version
	It can be used for block contents, recursive defines, or any text which has preprocessor syntax.
