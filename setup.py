# -*- coding: utf-8 -*-
from setuptools import find_packages, setup  # type: ignore

setup(
	name = "Preprocessor",
	version = "0.1",
	author = "Dorian Lesbre",
	url = "https://github.com/Lesbre/preprocessor/",
	description = "Preprocessor for text files (code/html/tex/...) inspired by the C preprocessor",
	package_dir = {"": "src"},
	packages = find_packages(),
)
