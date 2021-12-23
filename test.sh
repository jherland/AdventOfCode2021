#!/bin/sh

set -e -x

# Mypy does not yet handle all Python v3.10 features
mypy 01.py 03.py 04.py 06.py 07.py 08.py 09.py 10.py 11.py 12.py 14.py 15.py 16.py 17.py 18.py 19.py 20.py 21.py 22.py
black . --diff --color --check
pflake8
