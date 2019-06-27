# coding: utf-8
#
# Copyright (C) 2015-2019 ycmd contributors
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
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

from nose.tools import eq_
from hamcrest import ( assert_that,
                       contains,
                       empty,
                       has_entries )
import requests

from ycmd.utils import ReadFile
from ycmd.tests.python import PathToTestFile, SharedYcmd
from ycmd.tests.test_utils import ( CombineRequest,
                                    ParameterMatcher,
                                    SignatureMatcher,
                                    WithRetry )


def RunTest( app, test ):
  """
  Method to run a simple signature help test and verify the result

  test is a dictionary containing:
    'request': kwargs for BuildRequest
    'expect': {
       'response': server response code (e.g. httplib.OK)
       'data': matcher for the server response json
    }
  """
  contents = ReadFile( test[ 'request' ][ 'filepath' ] )

  app.post_json( '/event_notification',
                 CombineRequest( test[ 'request' ], {
                                 'event_name': 'FileReadyToParse',
                                 'contents': contents,
                                 } ),
                 expect_errors = True )

  # We ignore errors here and we check the response code ourself.
  # This is to allow testing of requests returning errors.
  response = app.post_json( '/signature_help',
                            CombineRequest( test[ 'request' ], {
                              'contents': contents
                            } ),
                            expect_errors = True )

  eq_( response.status_code, test[ 'expect' ][ 'response' ] )

  assert_that( response.json, test[ 'expect' ][ 'data' ] )


@SharedYcmd
def SignatureHelp_MethodTrigger_test( app ):
  RunTest( app, {
    'description': 'Trigger after (',
    'request': {
      'filetype'  : 'python',
      'filepath'  : PathToTestFile( 'general_fallback',
                                    'lang_python.py' ),
      'line_num'  : 6,
      'column_num': 10,
    },
    'expect': {
      'response': requests.codes.ok,
      'data': has_entries( {
        'errors': empty(),
        'signature_help': has_entries( {
          'activeSignature': 0,
          'activeParameter': 0,
          'signatures': contains(
            SignatureMatcher( 'def hack( obj )',
                              [ ParameterMatcher( 'obj' ) ] )
          ),
        } ),
      } )
    }
  } )


@SharedYcmd
def SignatureHelp_MultipleParameters_test( app ):
  RunTest( app, {
    'description': 'Trigger after ,',
    'request': {
      'filetype'  : 'python',
      'filepath'  : PathToTestFile( 'signature_help.py' ),
      'line_num'  : 14,
      'column_num': 50,
    },
    'expect': {
      'response': requests.codes.ok,
      'data': has_entries( {
        'errors': empty(),
        'signature_help': has_entries( {
          'activeSignature': 0,
          'activeParameter': 1,
          'signatures': contains(
            SignatureMatcher( 'def MultipleArguments( a, b, c )',
                              [ ParameterMatcher( 'a' ),
                                ParameterMatcher( 'b' ),
                                ParameterMatcher( 'c' ) ] )
          ),
        } ),
      } )
    }
  } )


@SharedYcmd
def SignatureHelp_CallWithinCall_test( app ):
  RunTest( app, {
    'description': 'Trigger after , within a call-within-a-call',
    'request': {
      'filetype'  : 'python',
      'filepath'  : PathToTestFile( 'signature_help.py' ),
      'line_num'  : 14,
      'column_num': 43,
    },
    'expect': {
      'response': requests.codes.ok,
      'data': has_entries( {
        'errors': empty(),
        'signature_help': has_entries( {
          'activeSignature': 0,
          'activeParameter': 1,
          'signatures': contains(
            SignatureMatcher( 'def center( width, fillchar )',
                              [ ParameterMatcher( 'width' ),
                                ParameterMatcher( 'fillchar' ) ] )
          ),
        } ),
      } )
    }
  } )


@SharedYcmd
def SignatureHelp_Constructor_test( app ):
  RunTest( app, {
    'description': 'Trigger after , within a call-within-a-call',
    'request': {
      'filetype'  : 'python',
      'filepath'  : PathToTestFile( 'signature_help.py' ),
      'line_num'  : 14,
      'column_num': 61,
    },
    'expect': {
      'response': requests.codes.ok,
      'data': has_entries( {
        'errors': empty(),
        'signature_help': has_entries( {
          'activeSignature': 0,
          'activeParameter': 0,
          'signatures': contains(
            SignatureMatcher( 'class Class( argument )',
                              [ ParameterMatcher( 'argument' ) ] )
          ),
        } ),
      } )
    }
  } )


@WithRetry
@SharedYcmd
def SignatureHelp_MultipleDefinitions_test( app ):
  RunTest( app, {
    'description': 'Jedi returns multiple signatures - both active',
    'request': {
      'filetype'  : 'python',
      'filepath'  : PathToTestFile( 'signature_help.py' ),
      'line_num'  : 30,
      'column_num': 27,
    },
    'expect': {
      'response': requests.codes.ok,
      'data': has_entries( {
        'errors': empty(),
        'signature_help': has_entries( {
          'activeSignature': 0,
          'activeParameter': 2,
          'signatures': contains(
            SignatureMatcher( 'def MultipleDefinitions( a, b, c )',
                              [ ParameterMatcher( 'a' ),
                                ParameterMatcher( 'b' ),
                                ParameterMatcher( 'c' ) ] ),

            SignatureMatcher( 'def MultipleDefinitions( many,'
                                                      ' more,'
                                                      ' arguments,'
                                                      ' to,'
                                                      ' this,'
                                                      ' one )',
                              [ ParameterMatcher( 'many' ),
                                ParameterMatcher( 'more' ),
                                ParameterMatcher( 'arguments' ),
                                ParameterMatcher( 'to' ),
                                ParameterMatcher( 'this' ),
                                ParameterMatcher( 'one' ) ] )
          ),
        } ),
      } )
    }
  } )


@WithRetry
@SharedYcmd
def SignatureHelp_MultipleDefinitions_OneActive_test( app ):
  RunTest( app, {
    'description': 'Jedi returns multiple signatures - both active',
    'request': {
      'filetype'  : 'python',
      'filepath'  : PathToTestFile( 'signature_help.py' ),
      'line_num'  : 30,
      'column_num': 30,
    },
    'expect': {
      'response': requests.codes.ok,
      'data': has_entries( {
        'errors': empty(),
        'signature_help': has_entries( {
          'activeSignature': 1,
          'activeParameter': 3,
          'signatures': contains(
            SignatureMatcher( 'def MultipleDefinitions( a, b, c )',
                              [ ParameterMatcher( 'a' ),
                                ParameterMatcher( 'b' ),
                                ParameterMatcher( 'c' ) ] ),

            SignatureMatcher( 'def MultipleDefinitions( many,'
                                                      ' more,'
                                                      ' arguments,'
                                                      ' to,'
                                                      ' this,'
                                                      ' one )',
                              [ ParameterMatcher( 'many' ),
                                ParameterMatcher( 'more' ),
                                ParameterMatcher( 'arguments' ),
                                ParameterMatcher( 'to' ),
                                ParameterMatcher( 'this' ),
                                ParameterMatcher( 'one' ) ] )

          ),
        } ),
      } )
    }
  } )
