#!/usr/bin/python3
# -*- coding: utf-8 -*-

from .preprocessor import Preprocessor


def blck_block(p: Preprocessor, args: str, contents: str) -> str:
	"""The block block. It does nothing but ensure post action
	declared in this block don't affect the rest of the file"""
	if args.strip() != "":
		p.send_error("the block block takes no arguments")
	return p.parse(contents)

def blck_verbatim(p: Preprocessor, args: str, contents: str) -> str:
	"""The verbatim block. It copies its content without parsing them
	Stops at first {% endverbatim %} not matching a {% verbatim %}"""
	if args.strip() != "":
		p.send_error("the verbatim block takes no arguments")
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
	contents = p.parse(contents)
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
			p.send_error('Multiple atlabel blocks with label "{}"'.format(lbl))
	else:
		p.command_vars["atlabel"] = dict()
	p.command_vars["atlabel"][lbl] = p.parse(contents)
	def place_block(pre: Preprocessor, string: str) -> str:
		if not lbl in pre.labels:
			pre.send_warning('No matching label for atlabel block "{}"'.format(lbl))
		indexes = pre.labels[lbl]
		for i in range(len(indexes)):
			string = pre.replace_string(
				indexes[i], indexes[i], string, p.command_vars["atlabel"][lbl], [], []
			)
		return string

	place_block.__doc__ = """Place the atlabel "{}" block at all labels""".format(lbl)
	place_block.__name__ = "place_atlabel_{}".format(lbl)
	p.post_actions.insert(0, place_block)
	return ""
