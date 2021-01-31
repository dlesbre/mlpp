# -*- coding: utf-8 -*-
from os import remove

from preproc import Preprocessor
from preproc.blocks import find_elifs_and_else


class TestCommands:

	file_name = "test_commands"

	def runtests(self, test, name):
		for i, j in enumerate(test):
			pre = Preprocessor()
			print("============= test {} ==============".format(i))
			in_str, out_str = j
			assert pre.process(in_str, name) == out_str

	def test_commands(self):
		name = "test_commands"
		test = [
			("{% file %}", name),
			("{% line %}\n\n\n{% line %}", "1\n\n\n4"),
			("h \n\n{% block %}{% line %}in sub{% endblock %}", "h \n\n3in sub"),
			("{% void %}{% def a \"booyouhou\n\" %}\n\n\n\n{% endvoid %}{% line %}{% a %}{% a %}{% line %}", "6booyouhou\nbooyouhou\n6"),
			("{% line %}{% repeat 5 %}\t\n{% endrepeat %}µ{% line %}", "1\t\n\t\n\t\n\t\n\t\nµ2"),
		]
		self.runtests(test, name)

	def test_def(self):
		test = [
			("{% def nom jean %}\nbonjour je suis {% nom %}","\nbonjour je suis jean"),
			("{% def nom\" jean\" %}\nbonjour je suis {% nom %}","\nbonjour je suis  jean"),
			("{% def nom\" \"\\\"jean\" %}\nbonjour je suis {% nom %}","\nbonjour je suis  \"\"jean"),
			("{% def nom jean %}{% def prenom nom %}\nbonjour je suis {% prenom %}","\nbonjour je suis nom"),
			("{% def nom jean %}{% def prenom {% nom %} %}\nbonjour je suis {% prenom %}","\nbonjour je suis jean"),
			("{% def add(a,b,c) (a+b+2c) %}hello{% add 1 2 3 %}", "hello(1+2+2c)"),
			("{% def add(pha,alpha,lpha) (pha,alpha)lpha %}hello{% add 1 2 3 %}", "hello(1,2)3"),
			("{% def f(a,b) a+b %}{% def f(a) {% f a 0 %} %}{% f 1 2 %}; {% f 1 %}", "1+2; 1+0"),
		]
		self.runtests(test, "test_def")

	def test_begin_end(self):
		test = [
			("{% begin %}", "{%"),
			("{% end %}", "%}"),
			("{% begin 12 %}", "{% begin 11 %}"),
			("{% call foo bar ...\t %}", "{% foo bar ... %}"),
			("{% def hello {% begin 1 %} %}{% hello %}", "{%"),
			("{% def foo bar %}{% def hello {% begin %}foo{% end %} %}{% hello %}", "bar"),
			("{% def foo bar %}{% def foo2 {% call foo %} %}{% foo2 %}{% def foo yoyo %}{% foo2 %}", "baryoyo"),
		]
		self.runtests(test, "test_begin_end")

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
		self.runtests(test, "test_strips")

	def test_include(self):
		path = "test.out"
		test = [
			("hello", "bonjour:{% include test.out %}:guten tag", "bonjour:hello:guten tag"),
			("{% def a b %}", "bonjour:{% include test.out %}:{% a %}", "bonjour::b"),
			("{% def a b %}{% c %}", "bonjour{% def c d %}:{% include test.out %}:{% a %}", "bonjour:d:b"),
			("{% def a b %}{% c %}", "bonjour{% def c d %}:{% include -v test.out %}:", "bonjour:{% def a b %}{% c %}:"),
			("<def a b><c>", "bonjour{% def c d %}:{% include -b < -e > test.out %}:{% a %}", "bonjour:d:b"),
		]
		for content, in_str, out_str in test:
			pre = Preprocessor()
			with open(path, "w") as file:
				file.write(content)
			assert pre.process(in_str, "test_include") == out_str
		remove(path)

	def test_replace(self):
		test = [
			("foofoobjf{% replace foo bar %}oofbifooj", "barbarbjbarfbibarj"),
			#("foo{% block %}{% replace foo bar %}foo yfoo{% endblock %}foo", "foobar ybarfoo"),
			("afoo{% replace foo bar %}{% replace aba yo %}fooabr", "yorbarabr"),
			("afoo{% replace --ignore-case foo bar %}FoOfOo FOO", "abarbarbar bar"),
			("{% replace -w foo bar %}foo(afoo1foo+foo foo foo", "bar(afoo1foo+bar bar bar"),
			("{% replace -w \"foo\" bar %}foo(afoo1foo+foo foo", "bar(afoo1foo+bar bar"),
			(r'{% replace -r "([a-z]+)" "low(\\1)" %}hello hio', "low(hello) low(hio)"),
			("{% replace -c 2 foo bar %}foo foo foo foo", "bar bar foo foo"),
			("{% replace foo bar \"foo yo bafoo\" %}", "bar yo babar"),
		]
		self.runtests(test, "test_replace")

	def test_upper(self):
		test = [
			("{% upper hello world %}", "HELLO WORLD"),
			("{% lower Hello WOrld %}", "hello world"),
			("{% capitalize hello world %}", "Hello world"),
			#("{% block %}some{% upper %} text{% endblock %} hello", "SOME TEXT hello"),
		]
		self.runtests(test, "test_upper")

	def test_for_deflist(self):
		test = [
			("{% for x in range(10) %}{% x %},{% endfor %}", "0,1,2,3,4,5,6,7,8,9,"),
			("{% for x in range(2,10) %}{% x %},{% endfor %}", "2,3,4,5,6,7,8,9,"),
			("{% for x in range(2_0,10) %}{% x %},{% endfor %}", ""),
			("{% for x in range(2_0,10,-1) %}{% x %},{% endfor %}", "20,19,18,17,16,15,14,13,12,11,"),
			("{% for x in  a\n b c \" def \" %}'{% x %}',{% endfor %}", "'a','b','c',' def ',"),
			("{% deflist list a b c d %}{% list 0 %}{% list -1 %}", "ad"),
			("{% deflist list a b c d %}{% deflist list2 1 2 3 4 %}"
			 "{% for x in range(4) %}{% list {% x %} %}{% list2 {% x %} %}{% endfor %}",
			 "a1b2c3d4"),
			("{% deflist names alice john frank %}{% deflist ages 23 31 19 %}\n"
			 "{% for i in range(3) %}{% names {% i %} %} (age {% ages {% i %} %})\n"
	     "{% endfor %}", "\nalice (age 23)\njohn (age 31)\nfrank (age 19)\n")
		]
		self.runtests(test, "test_for_deflist")

	def test_cut_paste(self):
		test = [
			("{% cut %}hello there!{% endcut %}hello:{% paste %}", "hello:hello there!"),
			("{% cut a %}content a{% endcut %}{% cut b %}content b{% endcut %}{% paste a %}{% paste b %}",
			 "content acontent b"),
			("{% def foo hi %}{% cut %}{% def foo bar1 %}{% endcut %}{% foo %}{% paste %}{% foo %}",
			 "hibar1"),
			("{% def foo hi %}{% cut --pre-render %}{% def foo bar1 %}{% endcut %}{% foo %}{% paste %}{% foo %}",
			 "bar1bar1"),
			("{% def foo hi %}{% cut %}{% def foo bar1 %}{% endcut %}{% foo %}{% paste --verbatim %}{% foo %}",
			 "hi{% def foo bar1 %}hi"),
			("{% cut %}foo is {% foo %}{% endcut %}\n"
	  	 "{% def foo bar %}\n"
	  	 "first paste: {% paste %}\n"
	  	 "{% def foo notbar %}\n"
	     "second paste: {% paste %}", "\n\nfirst paste: foo is bar\n\nsecond paste: foo is notbar"),
		]
		self.runtests(test, "test_cut_paste")

	def test_block(self):
		test = [
			("text{% void %}{% def name john %}hello this is a comment{% endvoid %}\n{% name %}", "text\njohn"),
			("{% verbatim %}{% hello %}{% endverbatim %}", "{% hello %}"),
			("{% verbatim %}some text with {% verbatim %}nested verbatim{% endverbatim %}{% endverbatim %}", "some text with {% verbatim %}nested verbatim{% endverbatim %}"),
			("{% repeat 5 %}yo{% endrepeat %}", "yoyoyoyoyo"),
			("{% label foo %}lala{% atlabel foo %}bar{% endatlabel %}yoyo{% label foo %}oups", "barlalayoyobaroups"),
			("{% atlabel yo %}bonjour{% endatlabel %}{% label yo %}", "bonjour"),
			("{% atlabel yo %}bjr{% endatlabel %}{% label yo %}..{% label yo %}", "bjr..bjr"),
			("{% atlabel yo %}bjrst{% endatlabel %}{% block %}hi{% label yo %}yy{% endblock %}", "hibjrstyy"),
			("{% atlabel yo %}bonjour{% endatlabel %}{% label yo %}***\n\n{% block %}nested:{% label yo %}{% endblock %}\n{% repeat 2 %}{% label yo %}{% endrepeat %}***{% label yo %}",
			 "bonjour***\n\nnested:bonjour\nbonjour***bonjour"
			)
		]
		self.runtests(test, "test_block")

	def test_if_find_elif(self):
		test_match = [
			("qmldkf", (-1,-1,None)),
			("abcd{% else %}defg", (4, 14, None)),
			("abcd{%  else\t\n %}defg", (4, 17, None)),
			("{% if something %}blad{%  else\t\n %}defg{% endif %}", (-1, -1, None)),
			("{% if something %}{% else %}{% endif %}{% else %}", (39, 49, None)),
			("{% elif something %}", (0, 20, " something ")),
		]
		for string, result in test_match:
			print("====== TEST ======")
			pre = Preprocessor()
			assert find_elifs_and_else(pre, string) == result

	def test_if(self):
		test = [
			("{% if def if %}hello{% endif %}", "hello"),
			("{% if not def if %}hello{% endif %}", ""),
			("{% def foo bar %}{% if {% foo %}==bar %}yes{% def foo nn %}{% endif %}{% foo %}", "yesnn"),
			("{% def foo bar %}{% if {% foo %}!=bar %}yes{% def foo nn %}{% endif %}{% foo %}", "bar"),
			("{% if ndef if %}hello{% else %}there{% endif %}", "there"),
			("{% if ndef if %}hello{% elif ndef def %}there{% elif def if %}general{% else %}kenobi{% endif %}", "general"),
			("\n{% if ndef if %}\n\n{% elif ndef def %}\n\n{% elif def if %}{% line %}\n{% else %}kenobi{% endif %}", "\n6\n"),
			("\n{% if ndef if %}\n\n{% elif ndef def %}some long test because reasons\n\n{% elif def if %}{% line %}\n{% else %}kenobi{% endif %}", "\n6\n"),
			("""{% def foo bar %}{% if def foo %}{% if {% foo %}!=bar %}{% def foo si %}{% else %}{% def foo la %}{% endif %}{% else %}no foo{% endif %}{% foo %}""", "la"),
		]
		self.runtests(test, "test_if")
