# Preprocessor

Simple program to preprocess text files. It is inspired by the C preprocessor and should work with any language.

## Preprocessor syntax

### Basic syntax

The preprocessor instructions are wrapped between "{% " and " %}" (note the space). These tokens can be changed if they conflict with the syntax of the file's langage.

Preprocessor instructions are split in three categories :

- **commands**: `{% command [args] %}`

	Commands print text where they are placed. For instance `{% date %}` prints the current date.
	Some special commands print no text but perform actions. `{% def name my_name %}` prints nothing but defines a new command `{% name %}` which prints `my_name`.
	
- **blocks**: `{% block_name [args] %} ... some text ... {% endblock_name %}`

	Blocks work very similarily to commands: they wrap around some text and alter it in some way. For instance the `{% verbatim %}` block prints all text in itself verbatim, without rendering any of the commands.
	
- **post_actions**: post action can be queued by special commands. They occur once every command and block in the current block has been rendered and affect the whole current block. For instance `{% replace foo bar %}` will replace all instances of "foo" with "bar" in the current block (including occurences before the command is called) but not occurences in higher blocks:

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

### Nesting and resolution order

Commands can be nested within one another : `{% foo {% bar %} %}`. The most innermost command is called first. So here `{% bar %}` is called, then `{% foo bar_output %}` is called. You can even do `{% {% foo %} %}` which will call `{% foo %}` first, then call `{% foo_output %}`. Note that this will fail if `foo_output` isn't a valid command, just like the previous command will fail is `bar_output` isn't a valid argument for `foo`.

Nesting can also be used for block arguments, but *it can NOT be used for block names and endblock*. This will likely fail block resolution and result in matching the wrong endblock or no endblock. 

### Command and block reference

Here follows a list of predefined commands, blocks and post_actions:

#### Commands

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

- `{% undef <identifier> %}` - undefines commands and blocks named identifier. You can undefine anything, including builtin commands and blocks.
- `{% label <label> %}` - prints no text and sets a label at current position

#### Blocks

- `{% block %}...{% endblock %}` - basic block, used to restrict post actions scope
- `{% verbatim %}...{% endverbatim %}` - copies its contents without parsing them. Stops at first `{% endverbatim %}` not matching a `{% verbatim %}`
- `{% repeat <number>0> %}...{% endrepeat %}` - renders its contents once and copies it *number* times.
- `{% atlabel <label> %}...{% endatlabel %}` - renders its contents but doesn't print them. As a post action, places a copy of the render at each occurence of *label*.

#### Post actions

These commands print nothing and trigger post actions

- `{% strip_empty_lines %}` - removes all empty lines (containing only whitespace) from current block
- `{% strip_trailing_whitespace %}` - removes all trailing whitespace (space, tabs,...) from the current block
- `{% strip_leading_whitespace %}` - removes leading whitespace (indent) from the current block
- `{% empty_last_line %}` - ensure the current block ends with a single empty (unless it is empty)
- `{% replace [-r|--regex] [-i|--ignore-case] [-w|--whole-word] "pattern" "replacement" %}` 
	replaces all occurences of pattern with replacement in the current block. 

	If the regex flag is present, pattern is a regex, replacement can contain `\1`, `\2` to place the groups captured by pattern
	
	If the whole-word flag is present, only replace occurrences which aren't part of a larger identifier (no letter/underscore before, no letter/underscore/number after).

## Developpement install

To install the package for developpement

1. Create a virtual environment

		python3 -m venv venv

2. Lauch the virtual env

		source venv/bin/activate

3. upgrade pip and install requirements

		python -m pip install --upgrade pip
		pip install -r requirements-devel.txt

4. Install the package

		pip install -e .

5. You're done! You import `Preprocessor` from python. You can also run tests with

		pytest
