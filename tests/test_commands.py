#!/usr/bin/python3
# -*- coding: utf-8 -*-

from Preprocessor import Preprocessor  # type: ignore


class TestCommands:

	pre = Preprocessor()

	def test_def(self):
		test = [
			("{% def nom jean %}\nbonjour je suis {% nom %}","\nbonjour je suis jean"),
			("{% def nom\" jean\" %}\nbonjour je suis {% nom %}","\nbonjour je suis  jean"),
			("{% def nom\" \"\\\"jean\" %}\nbonjour je suis {% nom %}","\nbonjour je suis  \"\"jean"),
			("{% def nom jean %}{% def prenom nom %}\nbonjour je suis {% prenom %}","\nbonjour je suis nom"),
			("{% def nom jean %}{% def prenom {% nom %} %}\nbonjour je suis {% prenom %}","\nbonjour je suis jean"),
		]
		for in_str, out_str in test:
			assert self.pre.parse(in_str) == out_str

	def test_begin_end(self):
		test = [
			("{% begin %}", "{% "),
			("{% end %}", " %}"),
			("{% begin 12 %}", "{% begin 11 %}"),
			("{% def hello {% begin 1 %} %}{% hello %}", "{% "),
			("{% def foo bar %}{% def hello {% begin %}foo{% end %} %}{% hello %}", "bar"),
		]
		for in_str, out_str in test:
			assert self.pre.parse(in_str) == out_str

	def test_strips(self):
		test = [
			("{% strip_empty_lines %}\n\t\nhello\n  \n  \nhi\n", "\nhello\nhi\n"),
			("{% strip_trailing_whitespace %}hello \n my name is john\t\t \nc\n", "hello\n my name is john\nc\n"),
			("{% strip_leading_whitespace %}hello \n  my name\n\t \t is john\n", "hello\nmy name\nis john\n"),
			("{% empty_last_line %}", ""),
			("{% empty_last_line %}hello", "hello\n"),
			("{% empty_last_line %}hello\n\n\n", "hello\n"),
		]
		for in_str, out_str in test:
			assert self.pre.parse(in_str) == out_str
		self.pre.post_actions = []

	def test_block(self):
		test = [
			("{% verbatim %}{% hello %}{% endverbatim %}", "{% hello %}"),
			("{% repeat 5 %}yo{% endrepeat %}", "yoyoyoyoyo"),
		]
		for in_str, out_str in test:
			assert self.pre.parse(in_str) == out_str
