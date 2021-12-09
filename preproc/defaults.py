"""
This module add all default commands/blocks/final_actions to
the Preprocessor class variables.
"""

from .blocks import *
from .commands import *
from .final_actions import *
from .preprocessor import Preprocessor

# default commands

Preprocessor.commands["def"] = cmd_def
Preprocessor.commands["undef"] = cmd_undef
Preprocessor.commands["deflist"] = cmd_deflist
Preprocessor.commands["begin"] = cmd_begin
Preprocessor.commands["end"] = cmd_end
Preprocessor.commands["call"] = cmd_call
Preprocessor.commands["label"] = cmd_label
Preprocessor.commands["date"] = cmd_date
Preprocessor.commands["include"] = cmd_include
Preprocessor.commands["error"] = cmd_error
Preprocessor.commands["warning"] = cmd_warning
Preprocessor.commands["version"] = cmd_version
Preprocessor.commands["filename"] = cmd_filename
Preprocessor.commands["line"] = cmd_line
Preprocessor.commands["paste"] = cmd_paste

Preprocessor.commands["strip_empty_lines"] = final_action_command(fnl_strip_empty_lines)
Preprocessor.commands["strip_leading_whitespace"] = final_action_command(fnl_strip_leading_whitespace)
Preprocessor.commands["strip_trailing_whitespace"] = final_action_command(fnl_strip_trailing_whitespace)
Preprocessor.commands["fix_last_line"] = final_action_command(fnl_fix_last_line)
Preprocessor.commands["fix_first_line"] = final_action_command(fnl_fix_first_line)
Preprocessor.commands["strip"] = cmd_strip
Preprocessor.commands["replace"] = cmd_replace
Preprocessor.commands["upper"] = cmd_upper
Preprocessor.commands["lower"] = cmd_lower
Preprocessor.commands["capitalize"] = cmd_capitalize

# default post action

Preprocessor.final_actions.append(fnl_atlabel)

# default blocks

Preprocessor.blocks["void"] = blck_void
Preprocessor.blocks["comment"] = blck_comment
Preprocessor.blocks["block"] = blck_block
Preprocessor.blocks["verbatim"] = blck_verbatim
Preprocessor.blocks["repeat"] = blck_repeat
Preprocessor.blocks["atlabel"] = blck_atlabel
Preprocessor.blocks["for"] = blck_for
Preprocessor.blocks["cut"] = blck_cut
Preprocessor.blocks["if"] = blck_if
