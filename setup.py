# -*- coding: utf-8 -*-
from setuptools import find_packages, setup  # type: ignore

with open("README.md", "r", encoding="utf-8") as fh:
	long_description = fh.read()

setup(
	name = "preprocessor",
	version = "0.0.1",
	author = "Dorian Lesbre",
	url = "https://github.com/Lesbre/preprocessor/",
	description = "Preprocessor for text files (code/html/tex/...) inspired by the C preprocessor",
	long_description = long_description,
	long_description_content_type = "text/markdown",
	package_dir = {"": "src"},
	packages = find_packages(), # ["src/preprocessor"]
	# scripts = ["preprocessor"],
	install_requires = [],
	extras_require = {
		"dev": ["pytest", "mypy"],
	},
	python_requires = ">=3.6",
	license = "MIT",
	classifiers = [
		"Programming Language :: Python :: 3",
		"License :: OSI Approved :: MIT License",
		"Operating System :: OS Independent",
	],
)
