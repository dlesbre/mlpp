#!/usr/bin/python3
# -*- coding: utf-8 -*-

from .preprocessor import *


def define(processor: Preprocessor, args_string : str) -> str:
	match = re.match(REGEX_IDENTIFIER, args_string)
	if match is None:
		raise CommandError(Position("", 0, 0), "Define has no valid command name")
	# identifier = match.group()

	return ""
