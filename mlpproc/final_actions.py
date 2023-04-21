"""
Definitions of default preprocessor final actions
and the commands that trigger them
"""
import argparse
import re
from typing import Optional

from .defs import REGEX_IDENTIFIER_WRAPPED, ArgumentParserNoExit
from .preprocessor import Command, Preprocessor


class FinalActionCommand(Command):
    """generates a simple command to add the final action function
    returns cmd which queues function to final actions.
    cmd.doc is generated by function.doc or function.__doc__"""

    name: Optional[str] = None

    # true_name = name if isinstance(name, str) else function.__name__.replace("fnl_", "")

    def final_action(self, preprocessor: Preprocessor, args_str: str) -> str:
        raise ValueError("Override in child classes")

    def __call__(self, preprocessor: Preprocessor, args_str: str) -> str:
        """Command queuing function as post action"""
        if args_str.strip() != "":
            preprocessor.send_warning(
                "extra-arguments", "{} takes no arguments".format(self.name)
            )
        preprocessor.final_actions.append(self.final_action)
        return ""


def final_action_replace(
    preprocessor: Preprocessor,
    string: str,
    pattern: str,
    replacement: str,
    flags: re.RegexFlag,
    count: int = 0,
) -> str:
    """same as string = re.sub(pattern, replacement, string)
    but uses preprocessor string_replace to offset labels correctly"""
    matches = []
    for re_match in re.finditer(pattern, string, flags=flags):
        matches.append((re_match.start(), re_match.end(), re_match.group()))
    replaced_nb = 0
    while matches:
        match = matches[0]
        local_repl = re.sub(pattern, replacement, match[2], flags=flags)
        string = preprocessor.replace_string(
            match[0], match[1], string, local_repl, matches
        )
        replaced_nb += 1
        if replaced_nb == count:
            return string
        if matches and match == matches[0]:
            del matches[0]
    return string


# ============================================================
# strip commands
# ============================================================


class Cmd_StripEmptyLines(FinalActionCommand):
    def final_action(self, preprocessor: Preprocessor, string: str) -> str:
        """final action to remove empty lines (containing whitespace only) from the text"""
        return final_action_replace(
            preprocessor, string, r"\n\s*\n", "\n", preprocessor.re_flags
        )

    doc = """
        Removes empty lines (lines containing only spaces)
        """


class Cmd_StripLeadingWhitespace(FinalActionCommand):
    def final_action(self, preprocessor: Preprocessor, string: str) -> str:
        """final action to remove leading whitespace (indent) from string"""
        return final_action_replace(preprocessor, string, "^[ \t]+", "", re.MULTILINE)

    doc = """
        Removes leading whitespace (indent)
        """


class Cmd_StripTrailingWhitespace(FinalActionCommand):
    def final_action(self, preprocessor: Preprocessor, string: str) -> str:
        """final action to remove trailing whitespace (indent) from string"""
        return final_action_replace(preprocessor, string, "[ \t]+$", "", re.MULTILINE)

    doc = """
        Removes trailing whitespace
        """


class Cmd_FixLastLine(FinalActionCommand):
    def final_action(self, preprocessor: Preprocessor, string: str) -> str:
        """final action to ensures file ends with an empty line if
        it is not empty"""
        if string and string[-1] != "\n":
            string += "\n"
        else:
            ii = len(string) - 2
            while ii >= 0 and string[ii] == "\n":
                ii -= 1
            string = preprocessor.replace_string(ii + 2, len(string), string, "", [])
        return string

    doc = """
        Ensures the file ends with a single empty
        line (unless it is empty)
        """


class Cmd_FixFirstLine(FinalActionCommand):
    def final_action(self, preprocessor: Preprocessor, string: str) -> str:
        """final action to ensures file starts with a non-empty
        non-whitespace line (if it is not empty)"""
        while string != "":
            pos = string.find("\n")
            if pos == -1:
                if string.isspace():
                    return preprocessor.replace_string(0, len(string), string, "", [])
                return string
            if string[: pos + 1].isspace():
                string = preprocessor.replace_string(0, pos + 1, string, "", [])
            else:
                break
        return string

    doc = """
        Ensures the document starts with a non-empty
        line (unless it is empty)
        """


class Cmd_Strip(Command):
    def __call__(self, preprocessor: Preprocessor, args: str) -> str:
        """the strip command
        queues:
        - fnl_strip_empty_lines
        - fnl_strip_leading_whitespace
        - fnl_strip_trailing_whitespace
        - fnl_fix_first_line
        - fnl_fix_last_line
        to preprocessor final actions"""
        if args.strip() != "":
            preprocessor.send_warning("extra-arguments", "strip takes no arguments")
        preprocessor.final_actions.append(Cmd_StripEmptyLines().final_action)
        preprocessor.final_actions.append(Cmd_StripLeadingWhitespace().final_action)
        preprocessor.final_actions.append(Cmd_StripTrailingWhitespace().final_action)
        preprocessor.final_actions.append(Cmd_FixFirstLine().final_action)
        preprocessor.final_actions.append(Cmd_FixLastLine().final_action)
        return ""

    doc = """
        Removes empty lines as well as trailing/leading whitespace.
        Ensures file ends on a single empty line
        """


# ============================================================
# replace command
# ============================================================


class Cmd_Replace(Command):
    parser = ArgumentParserNoExit(prog="replace", add_help=False)

    parser.add_argument("--regex", "-r", action="store_true")
    parser.add_argument("--ignore-case", "-i", action="store_true")
    parser.add_argument("--whole-word", "-w", action="store_true")
    parser.add_argument("--count", "-c", nargs="?", default=0, type=int)
    parser.add_argument("pattern")
    parser.add_argument("replacement")
    parser.add_argument("text", nargs="?", default=None, action="store")

    def __call__(self, preprocessor: Preprocessor, args: str) -> str:
        """the replace command
        usage: replace [-r|--regex] [-i|--ignore-case] [-w|--whole-word]
                    [-c|--count <number>] pattern replacement [text]
                if text is present, replace in text and print
                else queue final action to replace in current block
        """
        split = preprocessor.split_args(args)
        try:
            arguments = self.parser.parse_args(split)
        except argparse.ArgumentError:
            preprocessor.send_error(
                "invalid-argument",
                "invalid argument.\n"
                "usage: replace [-r|--regex] [-i|--ignore-case] [-w|--whole-word]\n"
                "               [-c|--count <number>] pattern replacement [text]",
            )
        flags = re.MULTILINE
        pattern: str = arguments.pattern
        repl = arguments.replacement
        if arguments.ignore_case:
            flags |= re.IGNORECASE
        if arguments.regex:
            if arguments.whole_word:
                preprocessor.send_error(
                    "invalid-argument",
                    "incompatible arguments : --regex and --whole-word",
                )
        else:
            pattern = re.escape(pattern)
            if arguments.whole_word:
                pattern = REGEX_IDENTIFIER_WRAPPED.format(pattern)
                repl = "\\1{}\\3".format(repl)
        count = arguments.count
        if count < 0:
            preprocessor.send_error(
                "invalid-argument",
                "invalid argument.\nthe replace --count argument must be positive",
            )
        pos = preprocessor.current_position.cmd_begin
        if arguments.text is not None:
            try:
                return re.sub(pattern, repl, arguments.text, count=count, flags=flags)
            except re.error as err:
                preprocessor.send_error(
                    "invalid-argument", "replace regex error: {}".format(err.msg)
                )
                return ""

        # no text, queue post action
        def fnl_replace(preprocessor: Preprocessor, string: str) -> str:
            try:
                return final_action_replace(
                    preprocessor, string, pattern, repl, flags, count=count
                )
            except re.error as err:
                preprocessor.context.update(pos)
                preprocessor.send_error(
                    "invalid-argument", "replace regex error: {}".format(err.msg)
                )
                preprocessor.context.pop()
                return ""

        fnl_replace.__name__ = "fnl_replace_lambda"
        fnl_replace.__doc__ = "final action for replace {}".format(args)
        preprocessor.final_actions.append(fnl_replace)
        return ""

    doc = """
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
                            in replacement with \\1, \\2,...
                            incompatible with --whole-word
        """


# ============================================================
# upper/lower/capitalize commands
# ============================================================


class Cmd_Upper(Command):
    def final_action(self, _: Preprocessor, string: str) -> str:
        """Final action for upper, transforms
        text in string to UPPER CASE"""
        return string.upper()

    def __call__(self, preprocessor: Preprocessor, args: str) -> str:
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
        preprocessor.final_actions.append(self.final_action)
        return ""

    doc = """
        Converts text to UPPER CASE

        usage: upper [text]

        If text is present, converts text
        else converts everything in the document (can be restricted with block).
        """


class Cmd_Lower(Command):
    def final_action(self, _: Preprocessor, string: str) -> str:
        """Final action for upper, transforms
        text in string to lower case"""
        return string.lower()

    def __call__(self, preprocessor: Preprocessor, args: str) -> str:
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
        preprocessor.final_actions.append(self.final_action)
        return ""

    doc = """
        Converts text to lower case

        usage: lower [text]

        If text is present, converts text
        else converts everything in the document (can be restricted with block).
        """


class Cmd_Capitalize(Command):
    def final_action(self, _: Preprocessor, string: str) -> str:
        """Final action for upper, transforms
        text in string to Capitalized Case"""
        return string.capitalize()

    def __call__(self, preprocessor: Preprocessor, args: str) -> str:
        """The capitalize command, switches text to lower case
        usage: capitalize [text]
                with text -> returns Text (ignores trailing/leading spaces)
                without   -> queues final action to transform all text in document
            (can be restricted with block) to Capitalized Case"""
        args = args.strip()
        if args:
            if len(args) >= 2 and args[0] == '"' and args[-1] == '"':
                args = args[0:-1]
            return args.capitalize()
        preprocessor.final_actions.append(self.final_action)
        return ""

    doc = """
        Converts text to Capitalized case

        usage: capitalize [text]

        If text is present, converts text
        else converts everything in the document (can be restricted with block).
        """
