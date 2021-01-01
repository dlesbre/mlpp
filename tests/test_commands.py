#!/usr/bin/python3
# -*- coding: utf-8 -*-

from Preprocessor import Preprocessor


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
