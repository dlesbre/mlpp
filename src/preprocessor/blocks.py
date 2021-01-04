# -*- coding: utf-8 -*-

from .preprocessor import Preprocessor


def blck_void(p: Preprocessor, args: str, contents: str) -> str:
	"""The void block, processes commands inside it but prints nothing"""
	if args.strip() != "":
		p.send_warning("the void block takes no arguments")
	p.context_update(p.current_position.end, "in void block")
	contents = p.parse(contents)
	p.context_pop()
	return ""

def blck_block(p: Preprocessor, args: str, contents: str) -> str:
	"""The block block. It does nothing but ensure post action
	declared in this block don't affect the rest of the file"""
	if args.strip() != "":
		p.send_warning("the block block takes no arguments")
	p.context_update(p.current_position.end, "in block block")
	contents = p.parse(contents)
	p.context_pop()
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
	p.context_update(p.current_position.end, "in block repeat")
	contents = p.parse(contents)
	p.context_pop()
	return contents * nb

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

	p.context_update(p.current_position.end, "in block atlabel")
	p.command_vars["atlabel"][lbl] = p.parse(contents)
	p.context_pop()
	return ""

def pst_atlabel(pre: Preprocessor, string: str) -> str:
	"""places atlabel blocks at all matching labels"""
	if "atlabel" in pre.command_vars:
		for lbl in pre.command_vars["atlabel"]:
			if not lbl in pre.labels:
				pre.send_warning('No matching label for atlabel block "{}"'.format(lbl))
			else:
				indexes = pre.labels[lbl]
				print(lbl, indexes)
				for i in range(len(indexes)):
					string = pre.replace_string(
						indexes[i], indexes[i], string, pre.command_vars["atlabel"][lbl], []
					)
				del pre.labels[lbl]
	return string
