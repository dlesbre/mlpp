# -*- coding: utf-8 -*-
import argparse
import re
from typing import Iterable

from .defs import REGEX_IDENTIFIER, REGEX_INTEGER, ArgumentParserNoExit
from .preprocessor import Preprocessor

# ============================================================
# simple blocks (void, block, verbatim)
# ============================================================


def blck_void(p: Preprocessor, args: str, contents: str) -> str:
	"""The void block, processes commands inside it but prints nothing"""
	if args.strip() != "":
		p.send_warning("the void block takes no arguments")
	p.context.update(p.current_position.end, "in void block")
	contents = p.parse(contents)
	p.context.pop()
	return ""

def blck_block(p: Preprocessor, args: str, contents: str) -> str:
	"""The block block. It does nothing but ensure post action
	declared in this block don't affect the rest of the file"""
	if args.strip() != "":
		p.send_warning("the block block takes no arguments")
	p.context.update(p.current_position.end, "in block block")
	contents = p.parse(contents)
	p.context.pop()
	return contents

def blck_verbatim(p: Preprocessor, args: str, contents: str) -> str:
	"""The verbatim block. It copies its content without parsing them
	Stops at first {% endverbatim %} not matching a {% verbatim %}"""
	if args.strip() != "":
		p.send_warning("the verbatim block takes no arguments")
	return contents

def blck_repeat(p: Preprocessor, args: str, contents: str) -> str:
	"""The repeat block.
	usage: repeat <number>
		renders its contents one and copies them number times"""
	args = args.strip()
	if not args.isnumeric():
		p.send_error("invalid argument. Usage: repeat [uint > 0]")
	nb = int(args)
	if nb <= 0:
		p.send_error("invalid argument. Usage: repeat [uint > 0]")
	p.context.update(p.current_position.end, "in block repeat")
	contents = p.parse(contents)
	p.context.pop()
	return contents * nb


# ============================================================
# atlabel block
# ============================================================


def blck_atlabel(p: Preprocessor, args: str, contents: str) -> str:
	"""the atlabel block
	usage: atlabel <label>
	renders its contents and stores them
	add a post action to place itself at all labels <label>"""
	lbl = args.strip()
	if lbl == "":
		p.send_error("empty label name")
	if "atlabel" in p.command_vars:
		if lbl in p.command_vars["atlabel"]:
			p.send_error('Multiple atlabel blocks with same label "{}"'.format(lbl))
	else:
		p.command_vars["atlabel"] = dict()

	p.context.update(p.current_position.end, "in block atlabel")
	p.command_vars["atlabel"][lbl] = p.parse(contents)
	p.context.pop()
	return ""

def fnl_atlabel(pre: Preprocessor, string: str) -> str:
	"""places atlabel blocks at all matching labels"""
	if "atlabel" in pre.command_vars:
		deletions = []
		for lbl in pre.command_vars["atlabel"]:
			if not lbl in pre.labels:
				pre.send_warning('No matching label for atlabel block "{}"'.format(lbl))
			else:
				indexes = pre.labels[lbl]
				for index in indexes:
					string = pre.replace_string(
						index, index, string, pre.command_vars["atlabel"][lbl], []
					)
				del pre.labels[lbl]
			deletions.append(lbl)
		for lbl in deletions:
			del pre.command_vars["atlabel"][lbl]
	return string


# ============================================================
# for block
# ============================================================

def to_int(string: str) -> int:
	"""convert a string matching REGEX_INTEGER to int"""
	return int(string.replace(" ", "").replace("_", ""))

def blck_for(pre: Preprocessor, args: str, contents: str) -> str:
	"""The for block, simple for loop
	usage: for <ident> in range(stop)
	                      range(start, stop)
	                      range(start, stop, step)
	       for <ident> in space separated list " argument with spaces"
	"""
	match = re.match(r"^\s*({})\s+in\s+".format(REGEX_IDENTIFIER), args)
	if match is None:
		pre.send_error(
			"Invalid syntax.\n"
			"usage: for <ident> in range(stop)\n"
	    "                      range(start, stop)\n"
			"                      range(start, stop, step)\n"
			"       for <ident> in space separated list \" argument with spaces\""
		)
		return ""
	ident = match.group(1)
	args = args[match.end():].strip()
	iterator: Iterable = []
	if args[0:5] == "range":
		regex = r"range\((?:\s*({nb})\s*,)?\s*({nb})\s*(?:,\s*({nb})\s*)?\)".format(
			nb = REGEX_INTEGER)
		match = re.match(regex, args)
		if match is None:
			pre.send_error(
				"Invalid range syntax in for.\n"
				"usage: range(stop) or range(start, stop) or range(start, stop, step)\n"
				"  start, stop and step, should be integers (contain only 0-9 or _, with an optional leading -)"
			)
			return ""
		groups = match.groups()
		start = 0
		step = 1
		stop = to_int(groups[1])
		if groups[0] is not None:
			start = to_int(groups[0])
			if groups[2] is not None:
				step = to_int(groups[2])
		iterator = range(start, stop, step)
	else:
		iterator = pre.split_args(args)
	result = ""
	for value in iterator:
		def defined_value(pr: Preprocessor, args: str) -> str:
			"""new command defined in for block"""
			if args.strip() != "":
				pr.send_warning(
					"Extra arguments.\nThe command {} defined in for loop takes no arguments".format(ident)
				)
			return str(value)
		defined_value.__name__ = "for_cmd_{}".format(ident)
		defined_value.__doc__ = "Command defined in for loop: {} = '{}'".format(ident, value)
		pre.commands[ident] = defined_value
		pre.context.update(pre.current_position.end, "in for block")
		result += pre.parse(contents)
		pre.context.pop()
	return result


# ============================================================
# cut block
# ============================================================


cut_parser = ArgumentParserNoExit(prog="cut", add_help=False)
cut_parser.add_argument("--pre-render", "-p", action="store_true")
cut_parser.add_argument("clipboard", nargs="?", default="")

def blck_cut(pre: Preprocessor, args: str, contents: str) -> str:
	"""the cut block.
	usage: cut [--pre-render|-p] [<clipboard_name>]
		if --pre-render - renders the block here
		  (will be rerendered at time of pasting, unless using paste -v|--verbatim)
		clipboard is a string identifying the clipboard, default is ""
	"""
	split = pre.split_args(args)
	try:
		arguments = cut_parser.parse_args(split)
	except argparse.ArgumentError:
		pre.send_error("invalid argument.\nusage: cut [--pre-render|-p] [<clipboard_name>]")
	clipboard = arguments.clipboard
	pos = pre.current_position.end
	context = pre.context.get_top().copy(pos, "in pasted block")
	if arguments.pre_render:
		pre.context.update(pos, "in cut block")
		contents = pre.parse(contents)
		pre.context.pop()
	if "clipboard" not in pre.command_vars:
		pre.command_vars["clipboard"] = {clipboard: (context, contents)}
	else:
		pre.command_vars["clipboard"][clipboard] = (context, contents)
	return ""
