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
