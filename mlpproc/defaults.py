"""
This module add all default commands/blocks/final_actions to
the Preprocessor class variables.
"""

from .blocks import (
    Blck_Atlabel,
    Blck_Block,
    Blck_Comment,
    Blck_Cut,
    Blck_For,
    Blck_If,
    Blck_Repeat,
    Blck_Verbatim,
    Blck_Void,
    Fnl_AtLabel,
)
from .commands import (
    Cmd_Begin,
    Cmd_Call,
    Cmd_Date,
    Cmd_Def,
    Cmd_Deflist,
    Cmd_End,
    Cmd_Error,
    Cmd_Filename,
    Cmd_FilePrettySize,
    Cmd_FileSize,
    Cmd_Include,
    Cmd_Label,
    Cmd_Line,
    Cmd_Paste,
    Cmd_Undef,
    Cmd_Version,
    Cmd_Warning,
)
from .final_actions import (
    Cmd_Capitalize,
    Cmd_FixFirstLine,
    Cmd_FixLastLine,
    Cmd_Lower,
    Cmd_Replace,
    Cmd_Strip,
    Cmd_StripEmptyLines,
    Cmd_StripLeadingWhitespace,
    Cmd_StripTrailingWhitespace,
    Cmd_Upper,
)
from .preprocessor import Preprocessor

# default commands

Preprocessor.commands["def"] = Cmd_Def()
Preprocessor.commands["undef"] = Cmd_Undef()
Preprocessor.commands["deflist"] = Cmd_Deflist()
Preprocessor.commands["begin"] = Cmd_Begin()
Preprocessor.commands["end"] = Cmd_End()
Preprocessor.commands["call"] = Cmd_Call()
Preprocessor.commands["label"] = Cmd_Label()
Preprocessor.commands["date"] = Cmd_Date()
Preprocessor.commands["include"] = Cmd_Include()
Preprocessor.commands["error"] = Cmd_Error()
Preprocessor.commands["warning"] = Cmd_Warning()
Preprocessor.commands["version"] = Cmd_Version()
Preprocessor.commands["filename"] = Cmd_Filename()
Preprocessor.commands["line"] = Cmd_Line()
Preprocessor.commands["paste"] = Cmd_Paste()
Preprocessor.commands["filesize"] = Cmd_FileSize()
Preprocessor.commands["fileprettysize"] = Cmd_FilePrettySize()

Preprocessor.commands["strip_empty_lines"] = Cmd_StripEmptyLines()
Preprocessor.commands["strip_leading_whitespace"] = Cmd_StripLeadingWhitespace()
Preprocessor.commands["strip_trailing_whitespace"] = Cmd_StripTrailingWhitespace()
Preprocessor.commands["fix_last_line"] = Cmd_FixLastLine()
Preprocessor.commands["fix_first_line"] = Cmd_FixFirstLine()
Preprocessor.commands["strip"] = Cmd_Strip()
Preprocessor.commands["replace"] = Cmd_Replace()
Preprocessor.commands["upper"] = Cmd_Upper()
Preprocessor.commands["lower"] = Cmd_Lower()
Preprocessor.commands["capitalize"] = Cmd_Capitalize()

# default post action

Preprocessor.final_actions.append(Fnl_AtLabel())

# default blocks

Preprocessor.blocks["void"] = Blck_Void()
Preprocessor.blocks["comment"] = Blck_Comment()
Preprocessor.blocks["block"] = Blck_Block()
Preprocessor.blocks["verbatim"] = Blck_Verbatim()
Preprocessor.blocks["repeat"] = Blck_Repeat()
Preprocessor.blocks["atlabel"] = Blck_Atlabel()
Preprocessor.blocks["for"] = Blck_For()
Preprocessor.blocks["cut"] = Blck_Cut()
Preprocessor.blocks["if"] = Blck_If()

__all__ = ("Preprocessor", "Cmd_Def")
