"""This module encodes a simple conditional
evaluation system"""

from typing import List

from .preprocessor import Preprocessor

SINGLE_CHAR_OPERATORS = "()"
DOUBLE_CHAR_OPERATORS = ["==", "!="]

def condition_lexer(string : str) -> List[str]:
	"""lexes the input string into a stream of tokens"""
	lexemes : List[str] = []
	in_string = False
	current_lexeme = ""
	str_len = len(string)
	i = 0
	while i < str_len:
		char = string[i]
		if in_string:
			if char == '"':
				in_string = False
				lexemes.append(current_lexeme)
				current_lexeme = ""
			else:
				current_lexeme += char
		else:
			# not in a string
			if char in SINGLE_CHAR_OPERATORS:
				if current_lexeme != "":
					lexemes.append(current_lexeme)
				lexemes.append(char)
				current_lexeme = ""
			elif i+1 < str_len and string[i:i+2] in DOUBLE_CHAR_OPERATORS:
				if current_lexeme != "":
					lexemes.append(current_lexeme)
				lexemes.append(string[i:i+2])
				current_lexeme = ""
				i += 1
			elif char == '"':
				if current_lexeme != "":
					lexemes.append(current_lexeme)
				current_lexeme = ""
				in_string = True
			elif char.isspace():
				if current_lexeme != "":
					lexemes.append(current_lexeme)
				current_lexeme = ""
			else:
				current_lexeme += char
		i += 1
	if current_lexeme:
		lexemes.append(current_lexeme)
	return lexemes

def find_matching_close_parenthese(tokens: List[str], start_index: int) -> int:
	"""finds the ")" matching the opening parenthese "(" found at
	tokens[start_index]. returns len(tokens) if none exists"""
	j = start_index + 1
	depth = 0
	len_tok = len(tokens)
	while j < len_tok:
		if tokens[j] == "(":
			depth += 1
		if tokens[j] == ")":
			depth -= 1
			if depth == -1:
				break
		j += 1
	return j

def condition_evaluator(preproc: Preprocessor, tokens: List[str]) -> bool:
	"""evaluates a string of tokens into a boolean"""
	i = 0
	len_tok = len(tokens)
	while i < len_tok:
		tok = tokens[i]
		if tok == "(":
			j = find_matching_close_parenthese(tokens, i)
			if j == len_tok:
				preproc.send_error("invalid-condition",
					"invalid condition syntax.\n"
					"Unmatched \"(\". (missing closing parenthese?)"
				)
			if i == 0 and j == len_tok-1:
				return condition_evaluator(preproc, tokens[1:-1])
			i = j
		elif tok == ")":
			preproc.send_error("invalid-condition",
				"invalid condition syntax.\n"
				"Unmatched \")\". (missing openning parenthese?)"
			)
		elif tok == "and":
			# uses python lazy evaluation
			return condition_evaluator(preproc, tokens[:i])\
				and condition_evaluator(preproc, tokens[i+1:])
		elif tok == "or":
			# uses python lazy evaluation
			return condition_evaluator(preproc, tokens[:i])\
				or condition_evaluator(preproc, tokens[i+1:])
		elif tok == "not":
			if i != 0:
				preproc.send_error("invalid-condition",
					'invalid condition syntax.\n'
					'"not" must be preceeded by "and", "or" or "("\n'
					'got "{} not"'.format(tokens[i-1])
				)
			return not condition_evaluator(preproc, tokens[1:])
		i += 1
	return simple_condition_evaluator(preproc, tokens)

def simple_condition_evaluator(preproc: Preprocessor, tokens: List[str]) -> bool:
	"""evaluates a string of tokens into a boolean,
	assumes the string of tokens doesn't contain "and", "or" and "not"
	"""
	len_tok = len(tokens)
	if len_tok == 1:
		return not(tokens[0] in ["false", "0", ""])
	if len_tok == 2:
		if tokens[0] == "def":
			return tokens[1] in preproc.commands or tokens[1] in preproc.blocks
		if tokens[0] == "ndef":
			return not (tokens[1] in preproc.commands or tokens[1] in preproc.blocks)
	if len_tok == 3:
		if tokens[1] == "==":
			return tokens[0] == tokens[2]
		if tokens[1] == "!=":
			return tokens[0] != tokens[2]
	preproc.send_error("invalid-condition",
		"invalid condition syntax.\n"
		"simple conditions are: \n"
		"  | true | false | 1 | 0 | <string>\n"
		"  | def <identifier> | ndef <identifier>\n"
		"  | <str> == <str> | <str> != <str>"
	)
	return False

def condition_eval(preproc: Preprocessor, string: str) -> bool:
	"""evaluates a condition.
	String must follow the condition syntax:

	simple_condition =
		| true | false | 1 | 0 | <string>
		| def <identifier> | ndef <identifier>
		| <str> == <str> | <str> != <str>

	condition =
		| <simple_condition> | not <simple_condition>
		| <condition> and <condition>
		| <condition> or <condition>
		| (<condition>)"""
	lexemes = condition_lexer(string)
	return condition_evaluator(preproc, lexemes)
