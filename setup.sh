#!/bin/bash -i
conda create --name oedenv
conda activate oedenv
conda install -c conda-forge pypy3.6
pypy3 -m ensurepip
pypy3 -m pip install --upgrade pip
pypy3 -m pip install pyparsing
