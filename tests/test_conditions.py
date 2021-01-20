from preproc.conditions import *
from preproc.defaults import Preprocessor


def test_lexer():
	test = [
		("a==b", ["a", "==", "b"]),
		("not a\tand\nb!=notop", ["not", "a", "and", "b", "!=", "notop"]),
		("allo=(d))not(b and c)", ["allo=", "(", "d", ")", ")", "not", "(", "b", "and", "c", ")"]),
	]
	for string, tokenlist in test:
		assert condition_lexer(string) == tokenlist

def test_conditions():
	preproc = Preprocessor()
	test = [
		("true", True),	("1", True),
		("\"\"", False), ("false", False), ("0", False),
		(" hello == \thello", True), (" hi == hello", False),
		(" hello != \thello", False), (" hi != hello", True),
		(" def label", True), (" def qffqfze", False),
		(" ndef label", False), (" ndef qffqfze", True),
		("(def label)", True), ("(a == a and b != a)", True),
	]
	for string, result in test:
		assert condition_eval(preproc, string) == result
		assert condition_eval(preproc, "not "+string) != result
		for o_string, o_result in test:
			assert condition_eval(preproc, string + " and " + o_string) == (result and o_result)
			assert condition_eval(preproc, string + " or " + o_string) == (result or o_result)
