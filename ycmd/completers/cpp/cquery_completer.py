# Copyright (C) 2017 ycmd contributors
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
import threading
from subprocess import PIPE

from ycmd import responses, utils
from ycmd.completers.language_server import language_server_completer

NO_DOCUMENTATION_MESSAGE = 'No documentation available for current context'

PATH_TO_CQUERY = os.path.abspath( os.path.join(
  os.path.dirname( __file__ ),
  '..',
  '..',
  '..',
  'third_party',
  'cquery',
  'build',
  'release',
  'bin',
  'cquery' ) )


_logger = logging.getLogger( __name__ )

def ShouldEnableCqueryCompleter():
  return bool( PATH_TO_CQUERY )


class CqueryCompleter( language_server_completer.LanguageServerCompleter ):
  def __init__( self, user_options ):
    super( CqueryCompleter, self ).__init__( user_options )

    self._server_keep_logfiles = user_options[ 'server_keep_logfiles' ]
    # Used to ensure that starting/stopping of the server is synchronized
    self._server_state_mutex = threading.RLock()

    self._connection = None
    self._server_handle = None
    self._server_stderr = None
    self._CleanUp()


  def SupportedFiletypes( self ):
    return [ 'c', 'cpp' ]


  def GetSubcommandsMap( self ):
    return {
      # Handled by base class
      'GoToDeclaration': (
        lambda self, request_data, args: self.GoToDeclaration( request_data )
      ),
      'GoTo': (
        lambda self, request_data, args: self.GoToDeclaration( request_data )
      ),
      'GoToReferences': (
        lambda self, request_data, args: self.GoToReferences( request_data )
      ),
      'GoToDefinition': (
        lambda self, request_data, args: self.GoToDeclaration( request_data )
      ),
      'FixIt': (
        lambda self, request_data, args: self.GetCodeActions( request_data,
                                                              args )
      ),
      'RefactorRename': (
        lambda self, request_data, args: self.RefactorRename( request_data,
                                                              args )
      ),

      # Handled by us
      'RestartServer': (
        lambda self, request_data, args: self._RestartServer( request_data )
      ),
      'StopServer': (
        lambda self, request_data, args: self._StopServer()
      ),
      'GetDoc': (
        lambda self, request_data, args: self.GetDoc( request_data )
      ),
      'GetType': (
        lambda self, request_data, args: self.GetType( request_data )
      ),
    }


  def GetConnection( self ):
    return self._connection


  def GetType( self, request_data ):
    hover_response = self.GetHoverResponse( request_data )
    try:
      get_type_clang = hover_response[ 0 ][ 'value' ]
    except:
      raise RuntimeError( 'Unknown type' )

    return responses.BuildDisplayMessageResponse( get_type_clang )


  def GetDoc( self, request_data ):
    hover_response = self.GetHoverResponse( request_data )
    documentation = ''
    if isinstance( hover_response, list ):
      for item in hover_response:
        if isinstance( item, str ):
          documentation += item + '\n'

    documentation = documentation.rstrip()

    if not documentation:
      raise RuntimeError( NO_DOCUMENTATION_MESSAGE )

    _logger.debug( 'doc = {}'.format(documentation))
    return responses.BuildDetailedInfoResponse( documentation )


  def DebugInfo( self, request_data ):
    items = [
      responses.DebugInfoItem( 'Cquery path', PATH_TO_CQUERY ),
    ]

    return responses.BuildDebugInfoResponse(
      name = "Cquery",
      servers = [
        responses.DebugInfoServer(
          name = "cquery C/C++ Language Server",
          handle = self._server_handle,
          executable = PATH_TO_CQUERY,
          extras = items
        )
      ] )


  def Shutdown( self ):
    self._StopServer()


  def ServerIsHealthy( self ):
    return self._ServerIsRunning()


  def _ServerIsRunning( self ):
    return utils.ProcessIsRunning( self._server_handle )


  def _RestartServer( self, request_data ):
    with self._server_state_mutex:
      self._StopServer()
      self._StartServer( request_data )


  def _CleanUp( self ):
    if not self._server_keep_logfiles:
      if self._server_stderr:
        utils.RemoveIfExists( self._server_stderr )
        self._server_stderr = None

    self._received_ready_message = threading.Event()
    self._server_init_status = 'Not started'
    self._server_started = False

    self._server_handle = None
    self._connection = None

    self.ServerReset()


  def HandleServerCommand( self, request_data, command ):
    if command[ 'command' ] == "cquery._applyFixIt":
      arguments = command[ 'arguments' ]
      return responses.FixIt(
        responses.Location( request_data[ 'line_num' ],
                            request_data[ 'column_num' ],
                            request_data[ 'filepath' ] ),
        language_server_completer.TextEditToChunks( request_data,
                                                    arguments[ 0 ],
                                                    arguments[ 1 ] ),
        command[ 'title' ] )
    return None


  def _StopServer( self ):
    with self._server_state_mutex:
      _logger.info( 'Shutting down cquery...' )
      # We don't use utils.CloseStandardStreams, because the stdin/out is
      # connected to our server connector. Just close stderr.
      #
      # The other streams are closed by the LanguageServerConnection when we
      # call Close.
      if self._server_handle and self._server_handle.stderr:
        self._server_handle.stderr.close()

      # Tell the connection to expect the server to disconnect
      if self._connection:
        self._connection.Stop()

      if not self._ServerIsRunning():
        _logger.info( 'cquery Language server not running' )
        self._CleanUp()
        return

      _logger.info( 'Stopping cquery server with PID {0}'.format(
                        self._server_handle.pid ) )

      try:
        self.ShutdownServer()

        # By this point, the server should have shut down and terminated. To
        # ensure that isn't blocked, we close all of our connections and wait
        # for the process to exit.
        #
        # If, after a small delay, the server has not shut down we do NOT kill
        # it; we expect that it will shut itself down eventually. This is
        # predominantly due to strange process behaviour on Windows.
        if self._connection:
          self._connection.Close()

        utils.WaitUntilProcessIsTerminated( self._server_handle,
                                            timeout = 15 )

        _logger.info( 'cquery Language server stopped' )
      except Exception:
        _logger.exception( 'Error while stopping cquery server' )
        # We leave the process running. Hopefully it will eventually die of its
        # own accord.

      # Tidy up our internal state, even if the completer server didn't close
      # down cleanly.
      self._CleanUp()


  def _StartServer( self, request_data ):
    with self._server_state_mutex:
      if self._server_started:
        return

      self._server_started = True

      _logger.info( 'Starting cquery Language Server...' )

      args = [ "--init={\"progressReportFrequencyMs\":-1,\"cacheDirectory\":\"/tmp\",\"completion\":{\"filterAndSort\":true}}",
               "--language-server",
               "--log-file",
               "/home/bstaletic/cquery.log" ]
      command = [ PATH_TO_CQUERY ] + args

      _logger.debug( 'Starting cquery-server with the following command: '
                     '{0}'.format( ' '.join( command ) ) )

      self._server_stderr = utils.CreateLogfile( 'cquery_stderr_' )
      with utils.OpenForStdHandle( self._server_stderr ) as stderr:
        self._server_handle = utils.SafePopen( command,
                                               stdin = PIPE,
                                               stdout = PIPE,
                                               stderr = stderr )

      if not self._ServerIsRunning():
        _logger.error( 'cquery Language Server failed to start' )
        return

      _logger.info( 'cquery Language Server started' )

      self._connection = (
        language_server_completer.StandardIOLanguageServerConnection(
          self._server_handle.stdin,
          self._server_handle.stdout,
          self.GetDefaultNotificationHandler() )
      )

      self._connection.Start()

      try:
        self._connection.AwaitServerConnection()
      except language_server_completer.LanguageServerConnectionTimeout:
        _logger.error( 'cquery failed to start, or did not connect '
                       'successfully' )
        self._StopServer()
        return

    self.SendInitialize( request_data )


  def OnFileReadyToParse( self, request_data ):
    self._StartServer( request_data )

    return super( CqueryCompleter, self ).OnFileReadyToParse( request_data )
