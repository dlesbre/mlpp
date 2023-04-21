"""
Definitions of default preprocessor blocks
"""
import argparse
import re
from typing import Any, Iterable, Optional, Tuple

from .conditions import condition_eval, find_matching_close_parenthese
from .defs import (
    REGEX_IDENTIFIER,
    REGEX_IDENTIFIER_END,
    REGEX_INTEGER,
    ArgumentParserNoExit,
    TokenMatch,
    to_integer,
)
from .preprocessor import Block, Command, Preprocessor

# ============================================================
# simple blocks (comment, void, block, verbatim)
# ============================================================


class Blck_Comment(Block):
    def __call__(self, preprocessor: Preprocessor, args: str, _contents: str) -> str:
        """The comment block, ignores its contents"""
        if args.strip() != "":
            preprocessor.send_warning(
                "extra-arguments", "the void block takes no arguments"
            )
        return ""

    doc = """
        This block is a comment.
        All text until the next 'endcomment' is ignored"""


class Blck_Void(Block):
    def __call__(self, preprocessor: Preprocessor, args: str, contents: str) -> str:
        """The void block, processes commands inside it but prints nothing"""
        if args.strip() != "":
            preprocessor.send_warning(
                "extra-arguments", "the void block takes no arguments"
            )
        preprocessor.context.update(preprocessor.current_position.end, "in void block")
        contents = preprocessor.parse(contents)
        preprocessor.context.pop()
        return ""

    doc = """
        This block is parsed but not printed.
        Use it to place comments or a bunch of def
        without adding whitespace"""


class Blck_Block(Block):
    parser = ArgumentParserNoExit(prog="block", add_help=False)
    parser.add_argument("--begin", "-b", nargs="?", default=None)
    parser.add_argument("--end", "-e", nargs="?", default=None)
    parser.add_argument("--local-defs", "-d", action="store_true")
    parser.add_argument("--local-actions", "-a", action="store_true")
    parser.add_argument("--local-clipboard", "-c", action="store_true")
    parser.add_argument("--local-labels", "-l", action="store_true")

    def __call__(self, preprocessor: Preprocessor, args: str, contents: str) -> str:
        """The block block. allows restriction of final actions, defs and
        clipboard to local block"""
        split = preprocessor.split_args(args)
        try:
            arguments = self.parser.parse_args(split)
        except argparse.ArgumentError:
            preprocessor.send_error(
                "invalid-argument",
                "invalid argument.\n"
                "usage: block [--begin|-b <str>] [--end|-e <str>]\n"
                "             [--local-actions|-a] [--local-defs|-d] [--local-clipboard|-c]",
            )
        begin = preprocessor.token_begin
        end = preprocessor.token_end
        if arguments.begin is not None:
            preprocessor.token_begin = arguments.begin
        if arguments.end is not None:
            preprocessor.token_end = arguments.end
        if arguments.local_defs:
            commands = preprocessor.commands.copy()
            blocks = preprocessor.blocks.copy()
            if "def" in preprocessor.command_vars:
                defs = preprocessor.command_vars["def"].copy()
            else:
                defs = dict()
        if arguments.local_clipboard:
            if "clipboard" in preprocessor.command_vars:
                clipboard = preprocessor.command_vars["clipboard"].copy()
            else:
                clipboard = dict()
        if arguments.local_actions:
            action = preprocessor.final_actions.copy()
            preprocessor.final_actions = Preprocessor.final_actions.copy()
        if arguments.local_labels:
            labels = preprocessor.labels.copy()

        preprocessor.context.update(preprocessor.current_position.end, "in block block")
        contents = preprocessor.parse(contents)
        preprocessor.context.pop()

        if arguments.local_actions:
            contents = preprocessor.run_final_actions(contents)
            preprocessor.final_actions = action
        if arguments.local_labels:
            preprocessor.labels = labels
            preprocessor.labels.new_level()  # add empty level to pop
        if arguments.local_defs:
            preprocessor.commands = commands
            preprocessor.blocks = blocks
            preprocessor.command_vars["def"] = defs
        if arguments.local_clipboard:
            preprocessor.command_vars["clipboard"] = clipboard

        preprocessor.token_begin = begin
        preprocessor.token_end = end
        return contents

    doc = """
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
        """


class Blck_Verbatim(Block):
    def __call__(self, preprocessor: Preprocessor, args: str, contents: str) -> str:
        """The verbatim block. It copies its content without parsing them
        Stops at first {% endverbatim %} not matching a {% verbatim %}"""
        if args.strip() != "":
            preprocessor.send_warning(
                "extra-arguments", "the verbatim block takes no arguments"
            )
        return contents

    doc = """
        Used to paste contents without parsing them
        Stops at first {% endverbatim %} not matching a {% verbatim %}.

        Ex:
        "{% verbatim %}some text with symbols {% and %}{% endverbatim %}"
        Prints:
        "some text with symbols {% and %}"

        Ex:
        "{% verbatim %}
            some text with {% verbatim %}nested verbatim{% endverbatim %}
        {% endverbatim %}"
        Prints:
        "
            some text with {% verbatim %}nested verbatim{% endverbatim %}
        "
        """


class Blck_Repeat(Block):
    def __call__(self, preprocessor: Preprocessor, args: str, contents: str) -> str:
        """The repeat block.
        usage: repeat <number>
                renders its contents one and copies them number times"""
        args = args.strip()
        if not args.isnumeric():
            preprocessor.send_error(
                "invalid-argument", "invalid argument. Usage: repeat [uint > 0]"
            )
        number = int(args)
        if number <= 0:
            preprocessor.send_error(
                "invalid-argument", "invalid argument. Usage: repeat [uint > 0]"
            )
        preprocessor.context.update(
            preprocessor.current_position.end, "in block repeat"
        )
        contents = preprocessor.parse(contents)
        preprocessor.context.pop()
        return contents * number

    doc = """
        Used to repeat a block of text a number of times

        Usage: repeat <number>

        Ex: "{% repeat 4 %}a{% endrepeat %}" prints "aaaa".

        Unlike {% for x in range(3) %}, {% repeat 3 %} only
        renders the block once and prints three copies.
        """


# ============================================================
# atlabel block
# ============================================================


class Blck_Atlabel(Block):
    def __call__(self, preprocessor: Preprocessor, args: str, contents: str) -> str:
        """the atlabel block
        usage: atlabel <label>
        renders its contents and stores them
        add a post action to place itself at all labels <label>"""
        lbl = args.strip()
        if lbl == "":
            preprocessor.send_error("invalid-label", "empty label name")
        if "atlabel" in preprocessor.command_vars:
            if lbl in preprocessor.command_vars["atlabel"]:
                preprocessor.send_error(
                    "atlabel-conflict",
                    'Multiple atlabel blocks with same label "{}"'.format(lbl),
                )
        else:
            preprocessor.command_vars["atlabel"] = dict()

        preprocessor.context.update(
            preprocessor.current_position.end, "in block atlabel"
        )
        preprocessor.command_vars["atlabel"][lbl] = preprocessor.parse(contents)
        preprocessor.context.pop()
        return ""

    doc = """
        Renders a chunk of text and places it at all labels matching
        its label when processing is done.

        Usage: atlabel <label>

        It differs from the cut block in that:
        - it will also print its content to calls of {% label XXX %} preceding it
        - it canno't be overwritting (at most one atlabel block per label)
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
        """


class Fnl_AtLabel(Command):
    def __call__(self, preprocessor: Preprocessor, string: str) -> str:
        """places atlabel blocks at all matching labels"""
        if "atlabel" in preprocessor.command_vars:
            deletions = []
            for lbl in preprocessor.command_vars["atlabel"]:
                nb_labels = len(preprocessor.labels.get_label(lbl))
                if nb_labels == 0:
                    preprocessor.send_warning(
                        "unplaced-atlabel",
                        'No matching label for atlabel block "{}"'.format(lbl),
                    )
                for i in range(nb_labels):
                    # use references to labels because of offsets
                    index = preprocessor.labels.get_label(lbl)[i]
                    string = preprocessor.replace_string(
                        index,
                        index,
                        string,
                        preprocessor.command_vars["atlabel"][lbl],
                        [],
                    )
                deletions.append(lbl)
            for lbl in deletions:
                del preprocessor.command_vars["atlabel"][lbl]
        return string


# ============================================================
# for block
# ============================================================


class Blck_For(Block):
    def __call__(self, preprocessor: Preprocessor, args: str, contents: str) -> str:
        """The for block, simple for loop
        usage: for <ident> in range(stop)
                            range(start, stop)
                            range(start, stop, step)
            for <ident> in space separated list " argument with spaces"
        """
        match = re.match(r"^\s*({})\s+in\s+".format(REGEX_IDENTIFIER), args)
        if match is None:
            preprocessor.send_error(
                "invalid-argument",
                "Invalid syntax.\n"
                "usage: for <ident> in range(stop)\n"
                "                      range(start, stop)\n"
                "                      range(start, stop, step)\n"
                '       for <ident> in space separated list " argument with spaces"',
            )
            return ""
        ident = match.group(1)
        args = args[match.end() :].strip()
        iterator: Iterable[Any] = []
        if args[0:5] == "range":
            regex = r"range\((?:\s*({nb})\s*,)?\s*({nb})\s*(?:,\s*({nb})\s*)?\)".format(
                nb=REGEX_INTEGER
            )
            match = re.match(regex, args)
            if match is None:
                preprocessor.send_error(
                    "invalid-argument",
                    "Invalid range syntax in for.\n"
                    "usage: range(stop) or range(start, stop) or range(start, stop, step)\n"
                    "  start, stop and step, should be integers (contain only 0-9 or _,"
                    " with an optional leading -)",
                )
                return ""
            groups = match.groups()
            start = 0
            step = 1
            stop = to_integer(groups[1])
            if groups[0] is not None:
                start = to_integer(groups[0])
                if groups[2] is not None:
                    step = to_integer(groups[2])
            iterator = range(start, stop, step)
        else:
            iterator = preprocessor.split_args(args)
        result = ""
        for value in iterator:

            class Defined_Value(Command):
                def __call__(self, preproc: Preprocessor, args: str) -> str:
                    """new command defined in for block"""
                    if args.strip() != "":
                        preproc.send_warning(
                            "extra-arguments",
                            (
                                "Extra arguments.\nThe command {} defined in for loop takes"
                                " no arguments"
                            ).format(ident),
                        )
                    return str(value)

                name = "for_cmd_{}".format(ident)
                doc = "Command defined in for loop: {} = '{}'".format(ident, value)

            preprocessor.commands[ident] = Defined_Value()
            preprocessor.context.update(
                preprocessor.current_position.end, "in for block"
            )
            result += preprocessor.parse(contents)
            preprocessor.context.pop()
        return result

    doc = """
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

        """


# ============================================================
# cut block
# ============================================================


class Blck_Cut(Block):
    parser = ArgumentParserNoExit(prog="cut", add_help=False)
    parser.add_argument("--pre-render", "-p", action="store_true")
    parser.add_argument("clipboard", nargs="?", default="")

    def __call__(self, preprocessor: Preprocessor, args: str, contents: str) -> str:
        """the cut block.
        usage: cut [--pre-render|-p] [<clipboard_name>]
                if --pre-render - renders the block here
                (will be rerendered at time of pasting, unless using paste -v|--verbatim)
                clipboard is a string identifying the clipboard, default is ""
        """
        split = preprocessor.split_args(args)
        try:
            arguments = self.parser.parse_args(split)
        except argparse.ArgumentError:
            preprocessor.send_error(
                "invalid-argument",
                "invalid argument.\nusage: cut [--pre-render|-p] [<clipboard_name>]",
            )
        clipboard = arguments.clipboard
        pos = preprocessor.current_position.end
        context = preprocessor.context.top.copy(pos, "in pasted block")
        if arguments.pre_render:
            preprocessor.context.update(pos, "in cut block")
            contents = preprocessor.parse(contents)
            preprocessor.context.pop()
        if "clipboard" not in preprocessor.command_vars:
            preprocessor.command_vars["clipboard"] = {clipboard: (context, contents)}
        else:
            preprocessor.command_vars["clipboard"][clipboard] = (context, contents)
        return ""

    doc = """
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
        """


# ============================================================
# if block
# ============================================================


class Blck_If(Block):
    def find_elifs_and_else(
        self, preproc: Preprocessor, string: str
    ) -> Tuple[int, int, Optional[str]]:
        """returns a tuple indicating the next elif/else:
        (-1,-1,None) -> no matching elif/else
        (begin, end, None) -> matching else at string[begin:end]
        (begin, end, str) -> matchin elif with arguments str at string[begin:end]"""
        tokens = preproc._find_tokens(string)
        depth = 0
        endif_regex = r"\s*{}if\s*{}".format(
            re.escape(preproc.token_endblock), re.escape(preproc.token_end)
        )
        if_regex = r"\s*if(?:{}|{})".format(
            re.escape(preproc.token_end), REGEX_IDENTIFIER_END
        )
        elif_regex = r"\s*(elif)(?:{}|{})".format(
            re.escape(preproc.token_end), REGEX_IDENTIFIER_END
        )
        else_regex = r"\s*else\s*{}".format(re.escape(preproc.token_end))
        for i, (begin, end, token) in enumerate(tokens):
            if token == TokenMatch.OPEN:
                if re.match(if_regex, string[end:], preproc.re_flags) is not None:
                    depth += 1
                elif re.match(endif_regex, string[end:], preproc.re_flags) is not None:
                    depth -= 1
                elif depth == 0:
                    match_else = re.match(else_regex, string[end:], preproc.re_flags)
                    match_elif = re.match(elif_regex, string[end:], preproc.re_flags)
                    if match_else is not None:
                        return (begin, end + match_else.end(), None)
                    if match_elif is not None:
                        parenthese = [
                            "(" if x[2] == TokenMatch.OPEN else ")" for x in tokens
                        ]
                        j = find_matching_close_parenthese(parenthese, i)
                        if j == len(tokens):
                            preproc.context.update(
                                begin + preproc.current_position.end, "in elif"
                            )
                            preproc.send_error(
                                "unmatched-open-token",
                                'Unmatched "{}" token in endif.\n'
                                'Add matching "{}" or use "{}begin{}" to place it.'.format(
                                    preproc.token_begin,
                                    preproc.token_end,
                                    preproc.token_begin,
                                    preproc.token_end,
                                ),
                            )
                            preproc.context.pop()
                        end += match_elif.end(1)
                        return (begin, tokens[j][1], string[end : tokens[j][0]])
        return (-1, -1, None)

    def __call__(self, preprocessor: Preprocessor, args: str, contents: str) -> str:
        """the if block
        usage: {% if <condition> %} ...
            [{% elif <condition> %} ...]
            [{% else %}...]
            {% endif %}
        """
        value = condition_eval(preprocessor, args)
        pos_0 = 0
        desc = "in if block"
        while True:
            else_info = self.find_elifs_and_else(preprocessor, contents[pos_0:])
            if value:
                endelse = pos_0 + else_info[0] if else_info[0] != -1 else len(contents)
                preprocessor.context.update(
                    pos_0 + preprocessor.current_position.end, desc
                )
                parsed = preprocessor.parse(contents[pos_0:endelse])
                preprocessor.context.pop()
                return parsed
            if else_info[0] == -1:
                # no matching else
                return ""
            if else_info[2] is None:
                value = not value
                desc = "in else"
            else:
                preprocessor.context.update(
                    pos_0 + else_info[0] + preprocessor.current_position.end,
                    "in elif evaluation",
                )
                args = preprocessor.parse(else_info[2])
                preprocessor.context.pop()
                value = condition_eval(preprocessor, args)
                desc = "in elif"
            pos_0 += else_info[1]

    doc = """
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
        """
