#!/bin/bash
# local install , dev only.
conda create -n test1 python=3.10
conda activate test1
python -m pip install --upgrade setuptools

python setup.py sdist
python setup.py bdist_wheel sdist
python setup.py install
