#!/usr/bin/python3
# -*- coding: utf-8 -*-
from os import remove

from preprocessor import Preprocessor  # type: ignore


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
			("{% strip_trailing_whitespace %}hello \n my name is johnd\t\t \nc\n", "hello\n my name is johnd\nc\n"),
			("{% strip_leading_whitespace %}hello \n  my name\n\t \t is johnc\n", "hello \nmy name\nis johnc\n"),
			("{% empty_last_line %}", ""),
			("{% empty_last_line %}hello", "hello\n"),
			("{% empty_last_line %}hello\n\n\n", "hello\n"),
		]
		for in_str, out_str in test:
			assert self.pre.parse(in_str) == out_str
		self.pre.post_actions = Preprocessor.post_actions.copy()

	def test_include(self):
		path = "test.out"
		test = [
			("hello", "bonjour:{% include test.out %}:guten tag", "bonjour:hello:guten tag"),
			("{% def a b %}", "bonjour:{% include test.out %}:{% a %}", "bonjour::b"),
			("{% def a b %}{% c %}", "bonjour{% def c d %}:{% include test.out %}:{% a %}", "bonjour:d:b"),
			("{% def a b %}{% c %}", "bonjour{% def c d %}:{% include -v test.out %}:{% a %}", "bonjour:{% def a b %}{% c %}:b"),
		]
		for content, in_str, out_str in test:
			with open(path, "w") as file:
				file.write(content)
			assert self.pre.parse(in_str) == out_str
		remove(path)

	def test_replace(self):
		test = [
			("foofoobjf{% replace foo bar %}oofbifooj", "barbarbjbarfbibarj"),
			("foo{% block %}{% replace foo bar %}foo yfoo{% endblock %}foo", "foobar ybarfoo"),
			("afoo{% replace foo bar %}{% replace aba yo %}fooabr", "yorbarabr"),
			("afoo{% replace --ignore-case foo bar %}FoOfOo FOO", "abarbarbar bar"),
			("{% replace -w foo bar %}foo(afoo1foo+foo foo", "bar(afoo1bar+bar bar"),
			("{% replace -w \"foo\" bar %}foo(afoo1foo+foo foo", "bar(afoo1bar+bar bar"),
			(r'{% replace -r "([a-z]+)" "low(\\1)" %}hello hio', "low(hello) low(hio)"),
		]
		for in_str, out_str in test:
			assert self.pre.parse(in_str) == out_str

	def test_block(self):
		test = [
			("{% verbatim %}{% hello %}{% endverbatim %}", "{% hello %}"),
			("{% repeat 5 %}yo{% endrepeat %}", "yoyoyoyoyo"),
			("{% label foo %}lala{% atlabel foo %}bar{% endatlabel %}yoyo{% label foo %}oups", "barlalayoyobaroups"),
		]
		for in_str, out_str in test:
			assert self.pre.parse(in_str) == out_str
