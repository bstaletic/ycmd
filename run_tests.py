#!/usr/bin/env python3

import argparse
import platform
import os
import glob
import subprocess
import os.path as p
import sys

BASE_PYTEST_ARGS = [ '-v', '--color=yes' ]

DIR_OF_THIS_SCRIPT = p.dirname( p.abspath( __file__ ) )
DIR_OF_THIRD_PARTY = p.join( DIR_OF_THIS_SCRIPT, 'third_party' )
LIBCLANG_DIR = p.join( DIR_OF_THIRD_PARTY, 'clang', 'lib' )

def Main():
  parser = argparse.ArgumentParser()
  group = parser.add_mutually_exclusive_group()
  parser.add_argument( '--valgrind',
                       action = 'store_true',
                       help = 'Run tests inside valgrind.' )

  parsed_args, extra_pytests_args = parser.parse_known_args()
  print( 'Running tests on Python', platform.python_version() )

  pytests_args = BASE_PYTEST_ARGS
  if extra_pytests_args:
    pytests_args.extend( extra_pytests_args )
  else:
    pytests_args += [ 'tests/clang/diagnostics_test.py::Diagnostics_ZeroBasedLineAndColumn_test' ]
  new_env = os.environ.copy()
  new_env[ 'PYTHONMALLOC' ] = 'malloc'
  new_env[ 'LD_LIBRARY_PATH' ] = LIBCLANG_DIR
  cmd = [ 'valgrind',
          '--gen-suppressions=all',
          '--error-exitcode=1',
          '--leak-check=full',
          '--show-leak-kinds=definite,indirect',
          '--errors-for-leak-kinds=definite,indirect' ]
  subprocess.check_call( cmd +
                         [ sys.executable, '-m', 'pytest' ] +
                         pytests_args,
                         env = new_env )


if __name__ == "__main__":
  Main()
