#!/bin/bash
python setup.py sdist
pip install check-manifest
python setup.py bdist_wheel sdist
twine upload dist/*

