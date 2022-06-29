#!/usr/bin/env bash
python setup.py bdist_wheel && twine upload dist/* -u $1 -p $2