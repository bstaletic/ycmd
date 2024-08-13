# Copyright (C) 2011-2020 ycmd contributors
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

import os
import logging

from ycmd.completers.language_server.language_server_completer import (
    LanguageServerCompleter,
    REQUEST_TIMEOUT_COMMAND,
    _LspLocationToLocationAndDescription )
from ycmd.completers.language_server import language_server_protocol as lsp
from ycmd import responses
from ycmd.utils import ( FindExecutable,
                         FindExecutableWithFallback,
                         LOGGER )
from ycmd import utils

PATH_TO_ROSLYN_OMNISHARP = os.path.join(
  os.path.abspath( os.path.dirname( __file__ ) ),
  '..', '..', '..', 'third_party', 'omnisharp-roslyn'
)
if utils.OnWindows():
  PATH_TO_OMNISHARP_ROSLYN_BINARY = os.path.join(
    PATH_TO_ROSLYN_OMNISHARP, 'OmniSharp.exe' )
else:
  PATH_TO_OMNISHARP_ROSLYN_BINARY = os.path.join(
    PATH_TO_ROSLYN_OMNISHARP, 'OmniSharp' )


def MonoRequired( roslyn_path: str ):
  return not utils.OnWindows() and roslyn_path.endswith( '.exe' )


def ShouldEnableCsCompleter( user_options ):
  user_roslyn_path = user_options[ 'roslyn_binary_path' ]
  if user_roslyn_path and not os.path.isfile( user_roslyn_path ):
    LOGGER.error( 'No omnisharp-roslyn executable at %s', user_roslyn_path )
    # We should trust the user who specifically asked for a custom path.
    return False

  if os.path.isfile( user_roslyn_path ):
    roslyn = user_roslyn_path
  else:
    roslyn = PATH_TO_OMNISHARP_ROSLYN_BINARY
  if not roslyn:
    return False

  if MonoRequired( roslyn ):
    mono = FindExecutableWithFallback( user_options[ 'mono_binary_path' ],
                                       FindExecutable( 'mono' ) )
    if not mono:
      LOGGER.info( 'No mono executable at %s', mono )
      return False

  return True


class CsharpCompleter( LanguageServerCompleter ):
  def __init__( self, user_options ):
    super().__init__( user_options )
    if os.path.isfile( user_options[ 'roslyn_binary_path' ] ):
      self._roslyn_path = user_options[ 'roslyn_binary_path' ]
    else:
      self._roslyn_path = PATH_TO_OMNISHARP_ROSLYN_BINARY
    self._mono = FindExecutableWithFallback( user_options[ 'mono_binary_path' ],
                                             FindExecutable( 'mono' ) )


  def GetServerName( self ):
    return 'OmniSharp-Roslyn'


  def GetProjectRootFiles( self ):
    return [ '*.csproj' ]


  def GetCommandLine( self ):
    # TODO: User options?
    cmdline = [ self._roslyn_path, '-lsp' ]
    if utils.LOGGER.isEnabledFor( logging.DEBUG ):
      cmdline += [ '-v' ]
    if MonoRequired( self._roslyn_path ):
      cmdline.insert( 0, self._mono )
    return cmdline


  def SupportedFiletypes( self ):
    return [ 'cs' ]


  def GetType( self, request_data ):
    hover_value = self.GetHoverResponse( request_data )[ 'value' ]
    if not hover_value:
      raise RuntimeError( 'No type found.' )
    value = hover_value.split( '\n', maxsplit = 2 )[ 1 ]
    return responses.BuildDisplayMessageResponse( value )


  def GetDoc( self, request_data ):
    hover_value = self.GetHoverResponse( request_data )[ 'value' ]
    if not hover_value:
      raise RuntimeError( 'No documentation available.' )
    # The response looks like this:
    #
    # ```csharp
    # type info
    # ```
    #
    # docstring
    #
    # The idea is to get rid of silly markdown backticks.
    lines = hover_value.splitlines()
    del lines[ 2 ]
    del lines[ 0 ]
    result = '\n'.join( lines )
    return responses.BuildDetailedInfoResponse( result )


  def GoToDocumentOutline( self, request_data ):
    if not self.ServerIsReady():
      raise RuntimeError( 'Server is initializing. Please wait.' )

    self._UpdateServerWithFileContents( request_data )

    request_id = self.GetConnection().NextRequestId()
    message = lsp.DocumentSymbol( request_id, request_data )
    response = self.GetConnection().GetResponse(
        request_id,
        message,
        REQUEST_TIMEOUT_COMMAND )

    result = response.get( 'result' ) or []
    result = _FlattenDocumentSymbolHierarchy( result )
    return _DocumentSymboListToGoTo( request_data, result )



def _DocumentSymboListToGoTo( request_data, symbols ):
  """Convert a list of LSP DocumentSymbol into a YCM GoTo response"""

  def BuildGoToLocationFromSymbol( symbol ):
    symbol[ 'uri' ] = lsp.FilePathToUri( request_data[ 'filepath' ] )
    location, line_value = _LspLocationToLocationAndDescription(
      request_data,
      symbol )

    description = ( f'{ lsp.SYMBOL_KIND[ symbol[ "kind" ] ] }: '
                    f'{ symbol[ "name" ] }' )

    goto = responses.BuildGoToResponseFromLocation( location,
                                                    description )
    goto[ 'extra_data' ] = {
      'kind': lsp.SYMBOL_KIND[ symbol[ 'kind' ] ],
      'name': symbol[ 'name' ],
    }
    return goto

  locations = [ BuildGoToLocationFromSymbol( s ) for s in
                sorted( symbols,
                        key = lambda s: ( s[ 'kind' ], s[ 'name' ] ) ) ]

  if not locations:
    raise RuntimeError( "Symbol not found" )
  elif len( locations ) == 1:
    return locations[ 0 ]
  else:
    return locations


def _FlattenDocumentSymbolHierarchy( symbols ):
  total = []
  for s in symbols:
    partial_results = [ s ]
    if s.get( 'children' ):
      partial_results.extend(
          _FlattenDocumentSymbolHierarchy( s[ 'children' ] ) )
    total.extend( partial_results )
  return total
