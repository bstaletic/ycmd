# encoding: utf-8
#
# Copyright (C) 2017-2018 ycmd contributors
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

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
from future import standard_library
standard_library.install_aliases()
from builtins import *  # noqa

import json
from future.utils import iterkeys
from pprint import pformat
from hamcrest import ( assert_that, contains, contains_inanyorder, has_entries,
                       has_entry )

from ycmd.tests.typescript import PathToTestFile, SharedYcmd
from ycmd.tests.test_utils import ( BuildRequest,
                                    LocationMatcher,
                                    RangeMatcher,
                                    WithRetry,
                                    WaitForDiagnosticsToBeReady,
                                    PollForMessagesTimeoutException,
                                    PollForMessages )
from ycmd.utils import ReadFile

MAIN_FILEPATH = PathToTestFile( 'test.ts' )
DIAG_MATCHERS_PER_FILE = {
  MAIN_FILEPATH: contains_inanyorder(
    has_entries( {
      'kind': 'ERROR',
      'text': "Property 'mA' does not exist on type 'Foo'. [2339]",
      'location': LocationMatcher( MAIN_FILEPATH, 17, 5 ),
      'location_extent': RangeMatcher( MAIN_FILEPATH, ( 17, 5 ), ( 17, 7 ) ),
      'ranges': contains( RangeMatcher( MAIN_FILEPATH, ( 17, 5 ), ( 17, 7 ) ) ),
      'fixit_available': False
    } ),
    has_entries( {
      'kind': 'ERROR',
      'text': "Property 'nonExistingMethod' does not "
              "exist on type 'Bar'. [2339]",
      'location': LocationMatcher( MAIN_FILEPATH, 35, 5 ),
      'location_extent': RangeMatcher( MAIN_FILEPATH, ( 35, 5 ), ( 35, 22 ) ),
      'ranges': contains( RangeMatcher( MAIN_FILEPATH,
                                        ( 35, 5 ),
                                        ( 35, 22 ) ) ),
      'fixit_available': False
    } ),
    has_entries( {
      'kind': 'ERROR',
      'text': 'Expected 1-2 arguments, but got 0. [2554]',
      'location': LocationMatcher( MAIN_FILEPATH, 37, 5 ),
      'location_extent': RangeMatcher( MAIN_FILEPATH, ( 37, 5 ), ( 37, 12 ) ),
      'ranges': contains( RangeMatcher( MAIN_FILEPATH,
                                        ( 37, 5 ),
                                        ( 37, 12 ) ) ),
      'fixit_available': False
    } ),
    has_entries( {
      'kind': 'ERROR',
      'text': "Cannot find name 'Bår'. [2304]",
      'location': LocationMatcher( MAIN_FILEPATH, 39, 1 ),
      'location_extent': RangeMatcher( MAIN_FILEPATH, ( 39, 1 ), ( 39, 5 ) ),
      'ranges': contains( RangeMatcher( MAIN_FILEPATH,
                                        ( 39, 1 ),
                                        ( 39, 5 ) ) ),
      'fixit_available': False
    } ),
    has_entries( {
      'kind': 'HINT',
      'text': "'a' is declared but its value is never read. [6133]",
      'location': LocationMatcher( MAIN_FILEPATH, 7, 5 ),
      'location_extent': RangeMatcher( MAIN_FILEPATH, ( 7, 5 ), ( 7, 6 ) ),
      'ranges': contains( RangeMatcher( MAIN_FILEPATH, ( 7, 5 ), ( 7, 6 ) ) ),
      'fixit_available': False
    } ),
  )
}


@SharedYcmd
def Diagnostics_FileReadyToParse_test( app ):
  filepath = PathToTestFile( 'test.ts' )
  contents = ReadFile( filepath )

  # It can take a while for the diagnostics to be ready.
  results = WaitForDiagnosticsToBeReady( app, filepath, contents, 'typescript' )
  print( 'completer response: {}'.format( pformat( results ) ) )

  assert_that( results, DIAG_MATCHERS_PER_FILE[ filepath ] )


@WithRetry
@SharedYcmd
def Diagnostics_DetailedDiagnostics_test( app ):
  filepath = PathToTestFile( 'test.ts' )
  contents = ReadFile( filepath )

  event_data = BuildRequest( filepath = filepath,
                             filetype = 'typescript',
                             contents = contents,
                             event_name = 'BufferVisit' )
  app.post_json( '/event_notification', event_data )

  diagnostic_data = BuildRequest( filepath = filepath,
                                  filetype = 'typescript',
                                  contents = contents,
                                  line_num = 35,
                                  column_num = 6 )

  assert_that(
    app.post_json( '/detailed_diagnostic', diagnostic_data ).json,
    has_entry(
      'message', "Property 'nonExistingMethod' does not exist on type 'Bar'."
    )
  )


@SharedYcmd
def Diagnostics_Poll_test( app ):
  filepath = PathToTestFile( 'test.ts' )
  contents = ReadFile( filepath )
  # Poll until we receive _all_ the diags asynchronously.
  to_see = sorted( iterkeys( DIAG_MATCHERS_PER_FILE ) )
  seen = {}

  try:
    for message in PollForMessages( app,
                                    { 'filepath': filepath,
                                      'contents': contents,
                                      'filetype': 'typescript' } ):
      print( 'Message {}'.format( pformat( message ) ) )
      if 'diagnostics' in message:
        if message[ 'diagnostics' ] == []:
          continue
        seen[ message[ 'filepath' ] ] = True
        if message[ 'filepath' ] not in DIAG_MATCHERS_PER_FILE:
          raise AssertionError(
            'Received diagnostics for unexpected file {}. '
            'Only expected {}'.format( message[ 'filepath' ], to_see ) )
        assert_that( message, has_entries( {
          'diagnostics': DIAG_MATCHERS_PER_FILE[ message[ 'filepath' ] ],
          'filepath': message[ 'filepath' ]
        } ) )

      if sorted( iterkeys( seen ) ) == to_see:
        break

      # Eventually PollForMessages will throw a timeout exception and we'll fail
      # if we don't see all of the expected diags.
  except PollForMessagesTimeoutException as e:
    raise AssertionError(
      str( e ) +
      'Timed out waiting for full set of diagnostics. '
      'Expected to see diags for {}, but only saw {}.'.format(
        json.dumps( to_see, indent=2 ),
        json.dumps( sorted( iterkeys( seen ) ), indent=2 ) ) )
