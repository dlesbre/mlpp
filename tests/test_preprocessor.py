#!/usr/bin/python3

from Preprocessor import *

class TestPreProcMethods:

	pre = Preprocessor()
	pre.token_begin = re.escape("(")
	pre.token_end = re.escape(")")

	def test_get_identifier_name(self):
		"""unit tests for Preprocessor.get_identifier_name"""
		tests = [
			("21", ""),
			("+*", ""),
			("hello21+3", "hello21"),
			("\t\n name ", "name"),
			("    _hidden_12||", "_hidden_12"),
		]
		for test_in, test_out in tests:
			assert self.pre.get_identifier_name(test_in) == test_out

	def test_find_tokens(self):
		"""Unit test for Preprovessor.find_tokens"""
		tests = [
			("()", [(0, TokenMatch.OPEN), (1, TokenMatch.CLOSE)]),
			(" ( ) ", [(1, TokenMatch.OPEN), (3, TokenMatch.CLOSE)]),
			("((()()))", [
				(0, TokenMatch.OPEN),
				(1, TokenMatch.OPEN),
				(2, TokenMatch.OPEN),
				(3, TokenMatch.CLOSE),
				(4, TokenMatch.OPEN),
				(5, TokenMatch.CLOSE),
				(6, TokenMatch.CLOSE),
				(7, TokenMatch.CLOSE),
			]),
		]
		for test_in, test_out in tests:
			assert self.pre.find_tokens(test_in) == test_out

	def test_find_matching_pair(self):
		"""Unit test for Preprovessor.find_matchin_pair"""
		tests = [
			([(0, TokenMatch.OPEN), (1, TokenMatch.CLOSE)], 0),
			([(1, TokenMatch.OPEN), (3, TokenMatch.CLOSE)], 0),
			([
				(0, TokenMatch.OPEN),
				(1, TokenMatch.OPEN),
				(2, TokenMatch.OPEN),
				(3, TokenMatch.CLOSE),
				(4, TokenMatch.OPEN),
				(5, TokenMatch.CLOSE),
				(6, TokenMatch.CLOSE),
				(7, TokenMatch.CLOSE)
			], 2),
			([(0, TokenMatch.CLOSE), (1, TokenMatch.OPEN)], -1),
		]
		for test_in, test_out in tests:
			assert self.pre.find_matching_pair(test_in) == test_out
