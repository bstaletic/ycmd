# Copyright (C) 2015-2018 ycmd contributors
#
# This file is part of ycmd.
#
# ycmd is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ycmd is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ycmd.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from __future__ import absolute_import
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

import os
import logging

from ycmd import utils
from ycmd.completers.language_server import simple_language_server_completer
from ycmd.utils import LOGGER

LOGFILE_FORMAT = 'tsserver_'
TSSERVER_DIR = os.path.abspath(
  os.path.join( os.path.dirname( __file__ ), '..', '..', '..', 'third_party',
                'tsserver' ) )


def FindServer( server_name ):
  # The TSServer executable is installed at the root directory on Windows while
  # it's installed in the bin folder on other platforms.
  for executable in [ os.path.join( TSSERVER_DIR, 'bin', server_name ),
                      os.path.join( TSSERVER_DIR, server_name ),
                      'tsserver' ]:
    server = utils.FindExecutable( executable )
    if server:
      return server
  return None


def ShouldEnableTypeScriptCompleter():
  tsserver = FindServer( 'typescript' )
  if not tsserver:
    LOGGER.error( 'Not using TypeScript completer: TSServer not installed '
                  'in %s', TSSERVER_DIR )
    return False
  lsp_server = FindServer( 'typescript-language-server' )
  if not lsp_server:
    LOGGER.error( 'Not using TypeScript completer: TSServer not installed '
                  'in %s', TSSERVER_DIR )
    return False
  LOGGER.info( 'Using TypeScript completer with %s', tsserver )
  return True


def _LogLevel():
  return 'verbose' if LOGGER.isEnabledFor( logging.DEBUG ) else 'normal'


class TypeScriptCompleter( simple_language_server_completer.SimpleLSPCompleter ):
  def GetServerName( self ):
    return 'TSServer'


  def GetProjectRootFiles( self ):
    return [ 'tsconfig.json', 'jsconfig.json' ]


  def GetCommandLine( self ):
    return [ FindServer( 'typescript-language-server' ),
             '--tsserver-path', FindServer( 'typescript' ),
             '--tsserver-log-file', self._stderr_file,
             '--tsserver-log-verbosity', _LogLevel(),
             '--stdio' ]


  def SupportedFiletypes( self ):
    return [ 'typescript', 'typescriptreact', 'javascript' ]

  def GetDoc( self, request_data ):
    return self.GetHoverResponse( request_data )[ 1 ]


  def GetType( self, request_data ):
    return self.GetHoverResponse( request_data )[ 0 ][ 'value' ]


  def GetCustomSubcommands( self ):
    return {
      'GetDoc': (
        lambda self, request_data, args: self.GetDoc( request_data )
      ),
      'GetType': (
        lambda self, request_data, args: self.GetType( request_data )
      ),
    }
