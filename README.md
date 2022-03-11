# MLPProc : Markup Language Pre-Preprocessor

Simple program to preprocess text files. It is inspired by the C preprocessor and should work with any language.

## Contents

- [Contents](#contents)
- [Installation](#installation)
- [Manual installation](#manual-installation)
- [Preprocessor syntax](#preprocessor-syntax)
  - [Basic syntax](#basic-syntax)
  - [Nesting and resolution order](#nesting-and-resolution-order)
- [Command line usage](#command-line-usage)
- [Python usage](#python-usage)
- [Command and block reference](#command-and-block-reference)
  - [Commands](#commands)
  - [Blocks](#blocks)
- [Defining commands, blocks and final actions](#defining-commands-blocks-and-final-actions)
  - [Useful functions](#useful-functions)

## Installation

This package has no dependencies. To install simply run
```
pip install mlpproc
```

Once installed you can call the preprocessor with
```
mlpp --version
python -m mlpproc --version
```

## Manual installation

For a manual installation run

```
git clone https://github.com/dlesbre/mlpproc.git &&
cd mlpproc &&
python3 -m venv venv &&
source venv/bin/activate &&
make setup
```

For development install, run `make setup-dev` to install extra dependencies and setup pre-commit.

## Preprocessor syntax

### Basic syntax

The preprocessor instructions are wrapped between "{%" and "%}". These tokens can be changed if they conflict with the syntax of the file's langage. Instructions are case sensitive.

Preprocessor instructions are split in three categories :

- **commands**: `{% command [args] %}`

	Commands print text where they are placed. For instance `{% date %}` prints the current date.
	Some special commands print no text but perform actions. `{% def name my_name %}` prints nothing but defines a new command `{% name %}` which prints `my_name`.

- **blocks**: `{% block_name [args] %} ... some text ... {% endblock_name %}`

	Blocks work very similarly to commands: they wrap around some text and alter it in some way. For instance the `{% verbatim %}` block prints all text in itself verbatim, without rendering any of the commands.

- **final actions**: some actions can be queued by special commands. They occur once every command and block in the file has been rendered and affect the whole current file. For instance `{% replace foo bar %}` will replace all instances of "foo" with "bar" in the whole rendered file (including occurrences before the command is called). Final actions can be restricted to a smaller part of the document with `{% block -a %}...{% endblock %}` :

		some text... foo here is not replaced
		{% begin block -a %}
			foo here is replaced
			{% replace foo bar %}
			foo here is replaced
			{% begin block %}
				foo here is also replaced
			{% endblock %}
			{% command foo as argument isn't replaced %}
			{% command that prints foo %} will be replaced
		{% endblock %}

For a list of command run `mlpp -h commands` or see the [command and block reference](#command-and-block-reference).

### Nesting and resolution order

Commands can be nested within one another : `{% foo {% bar %} %}`. The most innermost command is called first. So here `{% bar %}` is called, then `{% foo bar_output %}` is called. You can even do `{% {% foo %} %}` which will call `{% foo %}` first, then call `{% foo_output %}`. Note that this will fail if `foo_output` isn't a valid command, just like the previous command will fail is `bar_output` isn't a valid argument for `foo`.

Nesting can also be used for block arguments, but *it can NOT be used for block names and endblock*. This will likely fail block resolution and result in matching the wrong endblock or no endblock.

---

## Command line usage

The preprocessor can be called from the command line with:

	mlpp [--flags] [input_file]
	python3 -m mlpproc [--flags] [input_file]

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

The package can be imported in python 3 with `import mlpproc`. This imports a `Preprocessor` class with all default commands included (see [list](#command-and-block-reference)). The simplest way to use the preprocessor is then:

```Python
import mlpproc

preprocessor = mlpproc.Preprocessor()

parsed_contents = preprocessor.process(file_contents, filename)
```

The filename is only needed for pretty error reports, and can be

You can configure the preprocessor directly via it's public attributes:

- `max_recursion_depth: int` (default 20) - raises an error past this depth
- `token_begin: str` and `token_end: str` (default "{% " and " %}") - tokens wrapping preprocessor calls in the document. They should not be equal or be a single or double quote (`'` and `"`) or parentheses `(` or `)`.
- `token_endblock: str` (default "end") - specifies what form the endblock command takes with the regex `<token_begin>\s*<token_endblock><block_name>\s*<token_end>`
- `safe_calls: bool` (default True) - if True, catches exceptions raised by command or blocks
- `error_mode: mlpproc.ErrorMode` (default RAISE), how errors are handled:
	- PRINT_AND_EXIT -> print to stderr and exit
	- PRINT_AND_RAISE -> print to stderr and raise exception
	- RAISE -> raise exception
- `warning_mode: mlpproc.WarningMode` (default RAISE)
	- HIDE -> do nothing
	- PRINT -> print to stderr
	- RAISE -> raise python warning
	- AS_ERROR -> passes to self.send_error()
- `use_color: bool` (default False) if True, uses ansi color when printing errors



---

## Command and block reference

Here follows a list of predefined commands and blocks. An up-to-date list can be found by running `mlpp -h commands` and detailed descriptions obtained by running `mlpp -h <command_name>`.

### Commands

#### begin

```
  Prints the current begin token (default "{%")

  Usage: begin [<number>]
  The optional number is used for recursion calls
    begin     -> "{%"
    begin 0   -> "{%"
    begin <n> -> "{% begin <n-1> %}"
```

#### call

```
  Prints a call to its arguments.

  Ex: "{% call my_command my_args %}" -> "{% my_command my_args %}"
  Useful in defs to use recursive calls.
  For recursion you can stack calls:
  "{% call call ... %}" -> "{% call ... %}"
```

#### capitalize

```
  Converts text to Capitalized case

  usage: capitalize [text]

  If text is present, converts text
  else converts everything in the document (can be restricted with block).
```

#### date

```
  Prints the current date.

  Usage: date [format=YYYY-MM-DD]
    format specifies year with YYYY or YY, month with MM or M,
    day with DD or D, hour with hh or h, minutes with mm or m
    seconds with ss or s
```

#### def

```
  Defines a new command or macro.

  Usage:
   def foo               -> defines empty foo command (prints nothing)
   def foo   some text   -> {% foo %} prints "some text"
                            (strips trailing/leading space)
   def foo " some text " -> {% foo %} prints " some text "
   def foo(arg1, arg2) text with arg1 and arg2
      -> {% foo bar "hi there" %} prints "text with bar and hi there"

  def overwrites old commands and blocks irreversibly.
  All defs are global, including those coming from sub-blocks and included files.

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
```

#### deflist

```
  Defines a new command.

  Usage: deflist list_name space separated list " element with spaces "

  Defines list_name such that:
          list_name          prints the lists
          list_name <number> prints the n-th element
                             (number must be a between -length+1 and length+1)

  Can be used in combination with the for block to iterate multiple lists in a loop.
```

#### end

```
  Prints the current end token (default "%}")

  Usage: end [<number>]
  The optional number is used for recursion calls
    end     -> "%}"
    end 0   -> "%}"
    end <n> -> "{% end <n-1> %}"
```

#### error

```
  Raises an error.
  Use with if block to raise errors if conditions are not met.

  Usage: error [message]
```

#### filename

```
  Prints the name of the current file being parsed.
```

#### fix_first_line

```
  Ensures the document starts with a non-empty
  line (unless it is empty)
```

#### fix_last_line

```
  Ensures the file ends with a single empty
  line (unless it is empty)
```

#### include

```
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
```

#### input_name

```
  Prints name of input file
  (only defined when called via mlpp or mlpproc.__main__.preprocessor_main())
```

#### label

```
  Adds a label at the current position

  Usage: label <label_name>
  Where label_name must be a valid identifier.

  Can be used in combination with the atlabel block
  to place text at all occurrences of a label.
```

#### line

```
  Prints the current line number.
  This is the line number of the command in the input file, the line
  in the output file may differ due to insertions/deletions.
```

#### lower

```
  Converts text to lower case

  usage: lower [text]

  If text is present, converts text
  else converts everything in the document (can be restricted with block).
```

#### output_name

```
  Prints name of output file
  (only defined when called via mlpp or mlpproc.__main__.preprocessor_main())
```

#### paste

```
  Pastes the contents of a clipboard (defined in a cut block)

  Usage: paste [-v|--verbatim] [clipboard]
    if --verbatim is set, paste the text as is, without rendering it
    clipboard is a string identifying the clipboard (default "").
    it must match a previous cut block's clipboard argument
```

#### replace

```
  Used to find and replace text

  Usage: replace [--options] pattern replacement [text]

  If text is present, replacement takes place in text.
  else it takes place in the whole document (can be restricted with block)

  Options:
    -c --count <number> number of occurrences to replace (default all)
    -i --ignore-case    pattern search ignores case (foo will match foo,FoO,FOO...)
    -w --whole-word     pattern only matches full words, i.e. occurrences not directly
                        preceded/followed by a letter/number/underscore.
    -r --regex          pattern is a regular expression, capture groups can be placed
                        in replacement with \1, \2,...
                        incompatible with --whole-word
```

#### strip

```
  Removes empty lines as well as trailing/leading whitespace.
  Ensures file ends on a single empty line
```

#### strip_empty_lines

```
  Removes empty lines (lines containing only spaces)
```

#### strip_leading_whitespace

```
  Removes leading whitespace (indent)
```

#### strip_trailing_whitespace

```
  Removes trailing whitespace
```

#### undef

```
  Undefines a command or block.
  This is irreversible and can undefine built-in commands and blocks.

  Usage: undef name
```

#### version

```
  Prints the mlpp version.
```

#### warning

```
  Raises a warning.
  Use with if block to raise warnings if conditions are not met.

  Usage: warning [message]
```

### Blocks

#### atlabel

```
  Renders a chunk of text and places it at all labels matching
  its label when processing is done.

  Usage: atlabel <label>

  It differs from the cut block in that:
  - it will also print its content to calls of {% label XXX %} preceding it
  - it can't be overwriting (at most one atlabel block per label)
  - the text is rendered in the block (and not in where the text is pared)

  ex:
    "{% def foo bar %}
    first label: {% label my_label %}
    {% atlabel my_label %}foo is {% foo %}{% endatlabel %}
          {% def foo notbar %}
    second label: {% label my_label %}"
  prints:
    "
    first label: foo is bar

    second label: foo is bar"

  Can be used in combination with include to create files inheriting
  from a common base.
```

#### block

```
  Block used to restrict action/defs/labels... to a local part of the files
  Can be very useful to wrap an include

  usage: block [--options]

  options:
    -b --begin <string>  change the begin token (default is same as current)
    -e --end <string>    change the end token (default is same as current)
    -d --local-defs      commands defined and undefined in the block are local
    -a --local-actions   final actions called in the block will only affect the block
                         use this to restrict replace, upper, ... to a section
    -c --local-clipboard the clipboard defined by cut in the block are local
    -l --local-labels    labels defined in the block are local, so they can
                         only be written to by local atlabel blocks

  Just like the verbatim block, changing begin and end means that the block will
  end at the first {% endblock %} not matching a {% block %}:

    {% block -b < -e > %}
      {% block blabla %}
      ...
      {% endblock %} // this endblock is ignored
    {% endblock %} // block ends here
```

#### comment

```
  This block is a comment.
  All text until the next 'endcomment' is ignored
```

#### cut

```
  Used to cut a section of text to paste elsewhere.
  The text is processed when pasted, not when cut

  Usage: cut [--pre-render|-p] [<clipboard_name>]
    if --pre-render - renders the block here
      (will be rerendered at time of pasting, unless using paste -v|--verbatim)
    clipboard is a string identifying the clipboard, default is ""

  ex:
    {% cut %}foo is {% foo %}{% endcut %}
    {% def foo bar %}
    first paste: {% paste %}
    {% def foo notbar %}
    second paste: {% paste %}"
  prints:
    "

    first paste: foo is bar

    second paste: foo is notbar"
```

#### for

```
  Simple for loop used to render a chunk of text multiple times.
  ex: "{% for x in range(2) %}{% x %},{% endfor %}" -> "1,2,"

  Usage: for <ident> in range(stop)
                        range(start, stop)
                        range(start, stop, step)
         for <ident> in space separated list " argument with spaces"


  range can be combined with the deflist command to iterate multiple lists:

    "{% deflist names alice john frank %} {% deflist ages 23 31 19 %}
    {% for i in range(3) %}{% names {% i %} %} (age {% ages {% i %} %})
    {% endfor %}"

  prints:

    "
    alice (age 23)
    john (age 31)
    frank (age 19)
    "
```

#### if

```
  Used to select wether or not to render a chunk of text
  based on simple conditions
  ex :
    {% if def identifier %}, {% if ndef identifier %}...
    {% if {% var %}==str_value %}, {% if {% var %}!=str_value %}...

  Usage: {% if <condition> %} ...
         [{% elif <condition> %} ...]
         [{% else %}...]
         {% endif %}

  Condition syntax is as follows
    simple_condition =
      | true | false | 1 | 0 | <string>
      | def <identifier> | ndef <identifier>
      | <str> == <str> | <str> != <str>

    condition =
      | <simple_condition> | not <simple_condition>
      | <condition> and <condition>
      | <condition> or <condition>
      | (<condition>)
```

#### repeat

```
  Used to repeat a block of text a number of times

  Usage: repeat <number>

  Ex: "{% repeat 4 %}a{% endrepeat %}" prints "aaaa".

  Unlike {% for x in range(3) %}, {% repeat 3 %} only
    renders the block once and prints three copies.
```

#### verbatim

```
  Used to paste contents without parsing them
  Stops at first {% endverbatim %} not matching a {% verbatim %}.

  Ex:
    "{% verbatim %}some text with symbols {% and %}{% endverbatim %}"
  Prints:
    "some text with symbols {% and %}"

  Ex:
    "{% verbatim %}some text with {% verbatim %}nested verbatim{% endverbatim %}{% endverbatim %}"
  Prints:
    "some text with {% verbatim %}nested verbatim{% endverbatim %}"
```

#### void

```
  This block is parsed but not printed.
  Use it to place comments or a bunch of def
  without adding whitespace
```


---

## Defining commands, blocks and final actions

This package is designed to simply add new commands and blocks:

- **commands**: they are function with signature:
	```Python
	def command_func(p: Preprocessor, args: str) -> str
	```

	The first argument is the preprocessor object, the second is the args string entered after the command. For example when calling `{% command_name some args %}` args will contain `" some args "` including leading/trailing spaces.

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

	Actions are stored in the preprocessor's `final_actions` list, in the order in which they are to be executed. They can be added with:

	```Python
	# adds a post action to the whole class
	Preprocessor.final_actions.append(post_action_function)
	# adds a post action to a specific object
	preprocessor_obj.final_actions.append(post_action_function)
	```

	Adding block actions with commands to run in the current block is pretty simple via the `final_action_command` decorator:

	```Python
	def my_post_action(p: Preprocessor, args: str) -> str:
		# not added to Preprocessor.post_actions
		...

	Preprocessor.commands["run_my_post_action"] = final_action_command(my_post_action_command)
	```

### Useful functions

Some useful functions and attribute that are useful when defining commands or blocks

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
