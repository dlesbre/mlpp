# -*- coding: utf-8 -*-
from os import remove

from preprocessor import Context, Preprocessor  # type: ignore


class TestCommands:

	pre = Preprocessor()
	file_name = "my_file"

	def runtests(self, test):
		for in_str, out_str in test:
			self.pre.context_new(Context(self.file_name, in_str), 0)
			assert self.pre.parse(in_str) == out_str
			self.pre.context_pop()

	def test_commands(self):
		test = [
			("{% file %}", self.file_name),
			("{% line %}\n\n\n{% line %}", "1\n\n\n4"),
			("h \n\n{% block %}{% line %}in sub{% endblock %}", "h \n\n3in sub"),
			("{% void %}{% def a \"booyouhou\n\" %}\n\n\n\n{% endvoid %}{% line %}{% a %}{% a %}{% line %}", "6booyouhou\nbooyouhou\n6"),
			("{% line %}{% repeat 5 %}\t\n{% endrepeat %}µ{% line %}", "1\t\n\t\n\t\n\t\n\t\nµ2"),
		]
		self.runtests(test)

	def test_def(self):
		test = [
			("{% def nom jean %}\nbonjour je suis {% nom %}","\nbonjour je suis jean"),
			("{% def nom\" jean\" %}\nbonjour je suis {% nom %}","\nbonjour je suis  jean"),
			("{% def nom\" \"\\\"jean\" %}\nbonjour je suis {% nom %}","\nbonjour je suis  \"\"jean"),
			("{% def nom jean %}{% def prenom nom %}\nbonjour je suis {% prenom %}","\nbonjour je suis nom"),
			("{% def nom jean %}{% def prenom {% nom %} %}\nbonjour je suis {% prenom %}","\nbonjour je suis jean"),
			("{% def add(a,b,c) (a+b+2c) %}hello{% add 1 2 3 %}", "hello(1+2+23)"),
			("{% def add(pha,alpha,lpha) (pha,alpha)lpha %}hello{% add 1 2 3 %}", "hello(1,2)3"),
		]
		self.runtests(test)

	def test_begin_end(self):
		test = [
			("{% begin %}", "{% "),
			("{% end %}", " %}"),
			("{% begin 12 %}", "{% begin 11 %}"),
			("{% def hello {% begin 1 %} %}{% hello %}", "{% "),
			("{% def foo bar %}{% def hello {% begin %}foo{% end %} %}{% hello %}", "bar"),
		]
		self.runtests(test)

	def test_strips(self):
		test = [
			("{% strip_empty_lines %}\n\t\nhello\n  \n  \nhi\n", "\nhello\nhi\n"),
			("{% strip_trailing_whitespace %}hello \n my name is johnd\t\t \nc\n", "hello\n my name is johnd\nc\n"),
			("{% strip_leading_whitespace %}hello \n  my name\n\t \t is johnc\n", "hello \nmy name\nis johnc\n"),
			("{% fix_last_line %}", ""),
			("{% fix_last_line %}hello", "hello\n"),
			("{% fix_last_line %}hello\n\n\n", "hello\n"),
			("{% fix_first_line %}", ""),
			("{% fix_first_line %}\nhello", "hello"),
			("{% fix_first_line %}  \n\t\f\nhello\n\n\n", "hello\n\n\n"),
		]
		self.runtests(test)

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
			("{% replace -c 2 foo bar %}foo foo foo foo", "bar bar foo foo"),
		]
		self.runtests(test)

	def test_block(self):
		test = [
			("text{% void %}{% def name john %}hello this is a comment{% endvoid %}\n{% name %}", "text\njohn"),
			("{% verbatim %}{% hello %}{% endverbatim %}", "{% hello %}"),
			("{% repeat 5 %}yo{% endrepeat %}", "yoyoyoyoyo"),
			("{% label foo %}lala{% atlabel foo %}bar{% endatlabel %}yoyo{% label foo %}oups", "barlalayoyobaroups"),
		]
		self.runtests(test)
