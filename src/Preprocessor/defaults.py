#!/usr/bin/python3
# -*- coding: utf-8 -*-

from .blocks import *
from .commands import *
from .post_actions import *
from .preprocessor import Preprocessor

# default commands

Preprocessor.commands["def"] = cmd_def
Preprocessor.commands["undef"] = cmd_undef
Preprocessor.commands["begin"] = cmd_begin
Preprocessor.commands["end"] = cmd_end
Preprocessor.commands["label"] = cmd_label
Preprocessor.commands["date"] = cmd_date
Preprocessor.commands["include"] = cmd_include

Preprocessor.commands["strip_empty_lines"] = cmd_strip_empty_lines
Preprocessor.commands["strip_leading_whitespace"] = cmd_strip_leading_whitespace
Preprocessor.commands["strip_trailing_whitespace"] = cmd_strip_trailing_whitespace
Preprocessor.commands["empty_last_line"] = cmd_empty_last_line

# default post action

Preprocessor.post_actions.append(pst_atlabel)

# default blocks

Preprocessor.blocks["block"] = blck_block
Preprocessor.blocks["verbatim"] = blck_verbatim
Preprocessor.blocks["repeat"] = blck_repeat
Preprocessor.blocks["atlabel"] = blck_atlabel
