#!/usr/bin/env python3

import os
from os.path import abspath, dirname
import sys
import subprocess

if __name__ == "__main__":
    tests_dir = abspath(dirname(__file__))
    root = dirname(tests_dir)
    os.chdir(root)

    subprocess.check_call([sys.executable, "-m", "pytest"])
