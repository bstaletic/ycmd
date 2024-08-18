# Copyright (C) 2024 ycmd contributors
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

from hamcrest import assert_that, contains_exactly, equal_to, has_entry
from unittest.mock import patch
from unittest import TestCase

from ycmd.completers.language_server.language_server_completer import (
    LanguageServerConnectionTimeout )
from ycmd.tests.cs import ( PathToTestFile,
                            IsolatedYcmd,
                            StartCsCompleterServerInDirectory )
from ycmd.tests.test_utils import ( BuildRequest,
                                    MockProcessTerminationTimingOut,
                                    WaitUntilCompleterServerReady )


def AssertCsCompleterServerIsRunning( app, is_running ):
  request_data = BuildRequest( filetype = 'cs' )
  assert_that( app.post_json( '/debug_info', request_data ).json,
               has_entry(
                 'completer',
                 has_entry( 'servers', contains_exactly(
                   has_entry( 'is_running', is_running )
                 ) )
               ) )


class ServerManagementTest( TestCase ):
  @IsolatedYcmd()
  def test_ServerManagement_RestartServer( self, app ):
    filepath = PathToTestFile( 'Program.cs' )
    StartCsCompleterServerInDirectory( app, filepath )

    AssertCsCompleterServerIsRunning( app, True )

    app.post_json(
      '/run_completer_command',
      BuildRequest(
        filepath = filepath,
        filetype = 'cs',
        command_arguments = [ 'RestartServer' ],
      ),
    )

    WaitUntilCompleterServerReady( app, 'cs' )

    AssertCsCompleterServerIsRunning( app, True )


  @IsolatedYcmd()
  @patch( 'shutil.rmtree', side_effect = OSError )
  @patch( 'ycmd.utils.WaitUntilProcessIsTerminated',
          MockProcessTerminationTimingOut )
  def test_ServerManagement_CloseServer_Unclean( self, app, *args ):
    StartCsCompleterServerInDirectory( app, PathToTestFile() )

    app.post_json(
      '/run_completer_command',
      BuildRequest(
        filetype = 'cs',
        command_arguments = [ 'StopServer' ]
      )
    )

    request_data = BuildRequest( filetype = 'cs' )
    assert_that( app.post_json( '/debug_info', request_data ).json,
                 has_entry(
                   'completer',
                   has_entry( 'servers', contains_exactly(
                     has_entry( 'is_running', False )
                   ) )
                 ) )


  @IsolatedYcmd()
  def test_ServerManagement_StopServerTwice( self, app ):
    StartCsCompleterServerInDirectory( app, PathToTestFile() )

    app.post_json(
      '/run_completer_command',
      BuildRequest(
        filetype = 'cs',
        command_arguments = [ 'StopServer' ],
      ),
    )

    AssertCsCompleterServerIsRunning( app, False )

    # Stopping a stopped server is a no-op
    app.post_json(
      '/run_completer_command',
      BuildRequest(
        filetype = 'cs',
        command_arguments = [ 'StopServer' ],
      ),
    )

    AssertCsCompleterServerIsRunning( app, False )


  @IsolatedYcmd
  def test_ServerManagement_StartServer_Fails( self, app ):
    with patch( 'ycmd.completers.language_server.language_server_completer.'
                'LanguageServerConnection.AwaitServerConnection',
                side_effect = LanguageServerConnectionTimeout ):
      resp = app.post_json( '/event_notification',
                     BuildRequest(
                       event_name = 'FileReadyToParse',
                       filetype = 'cs',
                       filepath = PathToTestFile( 'Program.cs' ),
                       contents = ""
                     ) )

      assert_that( resp.status_code, equal_to( 200 ) )

      request_data = BuildRequest( filetype = 'cs' )
      assert_that( app.post_json( '/debug_info', request_data ).json,
                   has_entry(
                     'completer',
                     has_entry( 'servers', contains_exactly(
                       has_entry( 'is_running', False )
                     ) )
                   ) )
