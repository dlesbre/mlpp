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
	Stops at first {% endverbatim %} not matchin a {% verbatim %}"""
	if args.strip() != "":
		p.send_error("the verbatim block takes no arguments")
	return contents
