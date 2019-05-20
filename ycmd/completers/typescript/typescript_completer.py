# Copyright (C) 2019 ycmd contributors
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

import logging
import os

from ycmd import utils
from ycmd.completers.language_server import simple_language_server_completer

SERVER_EXEC = os.path.abspath(
  os.path.join( os.path.dirname( __file__ ), '..', '..', '..', 'third_party',
                'ts-js-lsp', 'lib', 'langserver-stdio.js' ) )

PATH_TO_NODE = utils.FindExecutable( 'node' )


def ShouldEnableJsTsCompleter( user_options ):
  server_exists = os.path.isfile( SERVER_EXEC )
  if server_exists:
    return True
  utils.LOGGER.info( 'No js/ts executable at %s.', SERVER_EXEC )
  return False


class JsTsCompleter( simple_language_server_completer.SimpleLSPCompleter ):
  def __init__( self, user_options ):
    super( JsTsCompleter, self ).__init__( user_options )


  def GetServerName( self ):
    return 'javascript-typescript-langserver'


  def GetCommandLine( self ):
    return [ PATH_TO_NODE, SERVER_EXEC ]


  def SupportedFiletypes( self ):
    return [ 'javascript', 'typescript' ]


  def GetCustomSubcommands( self ):
    return {
      'RestartServer': (
        lambda self, request_data, args: self._RestartServer( request_data )
      ),
    }
