# Preprocessor

Simple program to preprocess text files. It is inspired by the C preprocessor and should work with any language.

## Developpement install

To install the package for developpement

1. Create a virtual environment

		python3 -m venv venv

2. Lauch the virtual env

		source venv/bin/activate

3. upgrade pip and install requirements

		python -m pip install --upgrade pip
		pip install -r requirements-devel.txt

4. Install the package

		pip install -e .

5. You're done! You can run tests with

		pytest
