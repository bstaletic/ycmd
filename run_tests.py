#!/usr/bin/env python3

import os
import subprocess
import os.path as p
import sys


def Main():
  new_env = os.environ.copy()
  new_env[ 'PYTHONMALLOC' ] = 'malloc'
  cmd = [ 'valgrind',
          '--gen-suppressions=all',
          '--error-exitcode=1',
          '--leak-check=full',
          '--show-leak-kinds=definite,indirect',
          '--errors-for-leak-kinds=definite,indirect',
          sys.executable, '-m', 'pytest', '-v', '--color=yes', '--co' ]
  subprocess.check_call( cmd, env = new_env )


if __name__ == "__main__":
  Main()
