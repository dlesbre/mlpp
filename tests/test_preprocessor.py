#!/usr/bin/python3

from Preprocessor import *

class TestPreProcMethods:

	def test_get_identifier_name(arg):
		"""unit tests for Preprocessor.get_identifier_name"""
		print(arg)
		pre = Preprocessor()
		tests = [
			("21", ""),
			("+*", ""),
			("hello21+3", "hello21"),
			("\t\n name ", "name"),
			("    _hidden_12||", "_hidden_12"),
		]
		for test_in, test_out in tests:
			assert pre.get_identifier_name(test_in) == test_out
