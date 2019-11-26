# encoding: utf-8
#
# Copyright (C) 2018 ycmd contributors
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

from hamcrest import ( assert_that, contains, contains_inanyorder, has_entries,
                       has_entry )

from ycmd.tests.javascript import PathToTestFile, SharedYcmd
from ycmd.tests.test_utils import ( BuildRequest,
                                    LocationMatcher,
                                    RangeMatcher,
                                    WaitForDiagnosticsToBeReady,
                                    WithRetry )
from ycmd.utils import ReadFile


@SharedYcmd
def Diagnostics_FileReadyToParse_test( app ):
  filepath = PathToTestFile( 'test.js' )
  contents = ReadFile( filepath )

  event_data = BuildRequest( filepath = filepath,
                             filetype = 'javascript',
                             contents = contents,
                             event_name = 'BufferVisit' )
  app.post_json( '/event_notification', event_data )

  WaitForDiagnosticsToBeReady( app, filepath, contents, 'javascript' )
  event_data = BuildRequest( filepath = filepath,
                             filetype = 'javascript',
                             contents = contents,
                             event_name = 'FileReadyToParse' )

  assert_that(
    app.post_json( '/event_notification', event_data ).json,
    contains_inanyorder(
      has_entries( {
        'kind': 'ERROR',
        'text': "Property 'm' does not exist on type 'Foo'. [2339]",
        'location': LocationMatcher( filepath, 14, 5 ),
        'location_extent': RangeMatcher( filepath, ( 14, 5 ), ( 14, 6 ) ),
        'ranges': contains( RangeMatcher( filepath, ( 14, 5 ), ( 14, 6 ) ) ),
        'fixit_available': False
      } ),
      has_entries( {
        'kind': 'ERROR',
        'text': "Property 'nonExistingMethod' does not "
                "exist on type 'Bar'. [2339]",
        'location': LocationMatcher( filepath, 32, 5 ),
        'location_extent': RangeMatcher( filepath, ( 32, 5 ), ( 32, 22 ) ),
        'ranges': contains( RangeMatcher( filepath, ( 32, 5 ), ( 32, 22 ) ) ),
        'fixit_available': False
      } ),
      has_entries( {
        'kind': 'ERROR',
        'text': 'Expected 1-2 arguments, but got 0. [2554]',
        'location': LocationMatcher( filepath, 34, 5 ),
        'location_extent': RangeMatcher( filepath, ( 34, 5 ), ( 34, 12 ) ),
        'ranges': contains( RangeMatcher( filepath, ( 34, 5 ), ( 34, 12 ) ) ),
        'fixit_available': False
      } ),
      has_entries( {
        'kind': 'ERROR',
        'text': "Cannot find name 'Bår'. [2304]",
        'location': LocationMatcher( filepath, 36, 1 ),
        'location_extent': RangeMatcher( filepath, ( 36, 1 ), ( 36, 5 ) ),
        'ranges': contains( RangeMatcher( filepath, ( 36, 1 ), ( 36, 5 ) ) ),
        'fixit_available': False
      } ),
      has_entries( {
        'kind': 'HINT',
        'text': "Parameter 'foo' implicitly has an 'any' type,"
                " but a better type may be inferred from usage. [7044]",
        'location': LocationMatcher( filepath, 6, 5 ),
        'location_extent': RangeMatcher( filepath, ( 6, 5 ), ( 6, 8 ) ),
        'ranges': contains( RangeMatcher( filepath, ( 6, 5 ), ( 6, 8 ) ) ),
        'fixit_available': False
      } ),
      has_entries( {
        'kind': 'HINT',
        'text': "'foo' is declared but its value is never read. [6133]",
        'location': LocationMatcher( filepath, 6, 5 ),
        'location_extent': RangeMatcher( filepath, ( 6, 5 ), ( 6, 8 ) ),
        'ranges': contains( RangeMatcher( filepath, ( 6, 5 ), ( 6, 8 ) ) ),
        'fixit_available': False
      } ),
      has_entries( {
        'kind': 'HINT',
        'text': "Parameter 'bar' implicitly has an 'any' type,"
                " but a better type may be inferred from usage. [7044]",
        'location': LocationMatcher( filepath, 7, 5 ),
        'location_extent': RangeMatcher( filepath, ( 7, 5 ), ( 7, 8 ) ),
        'ranges': contains( RangeMatcher( filepath, ( 7, 5 ), ( 7, 8 ) ) ),
        'fixit_available': False
      } ),
      has_entries( {
        'kind': 'HINT',
        'text': "'bar' is declared but its value is never read. [6133]",
        'location': LocationMatcher( filepath, 7, 5 ),
        'location_extent': RangeMatcher( filepath, ( 7, 5 ), ( 7, 8 ) ),
        'ranges': contains( RangeMatcher( filepath, ( 7, 5 ), ( 7, 8 ) ) ),
        'fixit_available': False
      } ),
    )
  )


@WithRetry
@SharedYcmd
def Diagnostics_DetailedDiagnostics_test( app ):
  filepath = PathToTestFile( 'test.js' )
  contents = ReadFile( filepath )

  event_data = BuildRequest( filepath = filepath,
                             filetype = 'javascript',
                             contents = contents,
                             event_name = 'BufferVisit' )
  app.post_json( '/event_notification', event_data )

  diagnostic_data = BuildRequest( filepath = filepath,
                                  filetype = 'javascript',
                                  contents = contents,
                                  line_num = 32,
                                  column_num = 6 )

  assert_that(
    app.post_json( '/detailed_diagnostic', diagnostic_data ).json,
    has_entry(
      'message', "Property 'nonExistingMethod' does not exist on type 'Bar'."
    )
  )
