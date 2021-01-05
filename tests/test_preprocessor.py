# -*- coding: utf-8 -*-
from preprocessor import Context, Preprocessor, TokenMatch  # type: ignore


def test_context():
	s = """This is a string
With line breaks
and some unispired text"""
	a = Context("", s)
	assert a._line_breaks == [16, 33]
	line, char = a.line_number(s.find("some"))
	assert line == 3
	assert char == 5
	line, char = a.line_number(s.find("line"))
	assert line == 2
	assert char == 6
	a.add_dilatation(s.find("line"), 6)
	s = s.replace("line", "longerline")
	line, char = a.line_number(s.find("some"))
	assert line == 3
	assert char == 5
	line, char = a.line_number(s.find("line"))
	assert line == 2
	assert char == 6


class TestPreProcMethods:

	pre = Preprocessor()
	pre.token_begin = "("
	pre.token_end = ")"
	pre.token_endblock = "e"

	def test_get_identifier_name(self):
		"""unit tests for Preprocessor.get_identifier_name"""
		tests = [
			("21", ("", "", -1)),
			("+*", ("", "", -1)),
			("hello21+3", ("hello21", "+3", 7)),
			("\t\n name ", ("name", " ", 7)),
			("    _hidden_12||", ("_hidden_12", "||", 14)),
		]
		for test_in, test_out in tests:
			assert self.pre.get_identifier_name(test_in) == test_out

	def test_find_tokens(self):
		"""Unit test for Preprovessor.find_tokens"""
		tests = [
			("()", [(0,1, TokenMatch.OPEN), (1,2, TokenMatch.CLOSE)]),
			(" ( ) ", [(1,2, TokenMatch.OPEN), (3,4, TokenMatch.CLOSE)]),
			("((()()))", [
				(0,1, TokenMatch.OPEN),
				(1,2, TokenMatch.OPEN),
				(2,3, TokenMatch.OPEN),
				(3,4, TokenMatch.CLOSE),
				(4,5, TokenMatch.OPEN),
				(5,6, TokenMatch.CLOSE),
				(6,7, TokenMatch.CLOSE),
				(7,8, TokenMatch.CLOSE),
			]),
		]
		for test_in, test_out in tests:
			assert self.pre.find_tokens(test_in) == test_out

	def test_find_matching_pair(self):
		"""Unit test for Preprovessor.find_matchin_pair"""
		tests = [
			([(0,1, TokenMatch.OPEN), (1,2, TokenMatch.CLOSE)], 0),
			([(1,2, TokenMatch.OPEN), (3,4, TokenMatch.CLOSE)], 0),
			([(0,1, TokenMatch.OPEN), (1,2, TokenMatch.OPEN), (2,3, TokenMatch.CLOSE)], 1),
			([
				(0,1, TokenMatch.OPEN),
				(1,2, TokenMatch.OPEN),
				(2,3, TokenMatch.OPEN),
				(3,4, TokenMatch.CLOSE),
				(4,5, TokenMatch.OPEN),
				(5,6, TokenMatch.CLOSE),
				(6,7, TokenMatch.CLOSE),
				(7,8, TokenMatch.CLOSE)
			], 2),
			([(0,1, TokenMatch.CLOSE), (1,2, TokenMatch.OPEN)], -1),
		]
		for test_in, test_out in tests:
			assert self.pre.find_matching_pair(test_in) == test_out

	def test_find_matching_endblock(self):
		test = [
			("i", "(ei)", (0,4)),
			("i", "content (i args) content (ei) more content (ei)", (43, 47)),
			("i", "(i) (ei)(i args) (i) (ei)(ei) more content (ei)", (43, 47)),
			("i", "(i) foo (b) bar (eb) ctnt  (ei) more foo   (ei)", (43, 47)),
			("i", "content (i (i arges) blah (ei) args) (ei)t (ei)", (43, 47)),
			("i", "", (-1,-1)),
			("i", "(i) (ei)", (-1,-1)),
		]
		for arg0, arg1, rep in test:
			assert self.pre.find_matching_endblock(arg0, arg1) == rep

	def test_split_args(self):
		test = [
			(" foo -bar\t \"some string\" escaped\\ space", ["foo", "-bar", "some string", "escaped space"]),
      ("\nfoo \"string\\twith\\n\\\"escaped chars\"", ["foo", "string\twith\n\"escaped chars"]),
		]
		for arg, rep in test:
			assert self.pre.split_args(arg) == rep
