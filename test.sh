#!/bin/sh

set -e -x

# mypy
black . --diff --color --check
pflake8
