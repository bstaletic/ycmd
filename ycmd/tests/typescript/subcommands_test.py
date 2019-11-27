# encoding: utf-8
#
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

from __future__ import absolute_import
from __future__ import unicode_literals
from __future__ import print_function
from __future__ import division
# Not installing aliases from python-future; it's unreliable and slow.
from builtins import *  # noqa

from hamcrest import ( assert_that,
                       contains,
                       contains_inanyorder,
                       contains_string,
                       has_entries,
                       has_entry,
                       matches_regexp )
from mock import patch
from nose.tools import eq_
import os
import requests
import pprint

from ycmd.tests.typescript import IsolatedYcmd, PathToTestFile, SharedYcmd
from ycmd.tests.test_utils import ( BuildRequest,
                                    ChunkMatcher,
                                    CombineRequest,
                                    ExpectedFailure,
                                    ErrorMatcher,
                                    LocationMatcher,
                                    RangeMatcher,
                                    MessageMatcher,
                                    MockProcessTerminationTimingOut,
                                    WaitForDiagnosticsToBeReady,
                                    WaitUntilCompleterServerReady )
from ycmd.utils import ReadFile


def RunTest( app, test ):
  contents = ReadFile( test[ 'request' ][ 'filepath' ] )

  app.post_json(
    '/event_notification',
    CombineRequest( test[ 'request' ], {
      'contents': contents,
      'filetype': 'typescript',
      'event_name': 'BufferVisit'
    } )
  )

  app.post_json(
    '/event_notification',
    CombineRequest( test[ 'request' ], {
      'contents': contents,
      'filetype': 'typescript',
      'event_name': 'FileReadyToParse'
    } )
  )

  # We ignore errors here and check the response code ourself.
  # This is to allow testing of requests returning errors.
  response = app.post_json(
    '/run_completer_command',
    CombineRequest( test[ 'request' ], {
      'contents': contents,
      'filetype': 'typescript',
      'command_arguments': ( [ test[ 'request' ][ 'command' ] ]
                             + test[ 'request' ].get( 'arguments', [] ) )
    } ),
    expect_errors = True
  )

  print( 'completer response: {0}'.format( pprint.pformat( response.json ) ) )

  eq_( response.status_code, test[ 'expect' ][ 'response' ] )

  if not test.get( 'resolve_fixits', False ):
    assert_that( response.json, test[ 'expect' ][ 'data' ] )
  else:
    unresolved_fixits = response.json[ 'fixits' ]
    resolved_fixits = [
      app.post_json(
        '/resolve_fixit',
          CombineRequest( test[ 'request' ], {
            'contents': contents,
            'filetype': 'typescript',
            'fixit': f } )
      ).json for f in unresolved_fixits ]
    print( 'resolved fixits: {}'.format( pprint.pformat( resolved_fixits ) ) )
    assert_that( resolved_fixits, test[ 'expect' ][ 'data' ] )


@SharedYcmd
def Subcommands_DefinedSubcommands_test( app ):
  subcommands_data = BuildRequest( completer_target = 'typescript' )

  assert_that(
    app.post_json( '/defined_subcommands', subcommands_data ).json,
    contains_inanyorder(
      'ExecuteCommand',
      'Format',
      'GoTo',
      'GoToDeclaration',
      'GoToDefinition',
      'GoToImplementation',
      'GoToType',
      'GetDoc',
      'GetType',
      'GoToReferences',
      'FixIt',
      'OrganizeImports',
      'RefactorRename',
      'RestartServer'
    )
  )


@SharedYcmd
def Subcommands_Format_WholeFile_Spaces_test( app ):
  filepath = PathToTestFile( 'test.ts' )
  RunTest( app, {
    'description': 'Formatting is applied on the whole file '
                   'with tabs composed of 4 spaces',
    'request': {
      'command': 'Format',
      'filepath': filepath,
      'options': {
        'tab_size': 4,
        'insert_spaces': True
      }
    },
    'expect': {
      'response': requests.codes.ok,
      'data': has_entries( {
        'fixits': contains( has_entries( {
          'chunks': contains(
            ChunkMatcher( '    ',
                          LocationMatcher( filepath,  3,  1 ),
                          LocationMatcher( filepath,  3,  3 ) ),
            ChunkMatcher( '    ',
                          LocationMatcher( filepath,  4,  1 ),
                          LocationMatcher( filepath,  4,  3 ) ),
            ChunkMatcher( ' ',
                          LocationMatcher( filepath,  4, 14 ),
                          LocationMatcher( filepath,  4, 14 ) ),
            ChunkMatcher( '    ',
                          LocationMatcher( filepath,  5,  1 ),
                          LocationMatcher( filepath,  5,  3 ) ),
            ChunkMatcher( ' ',
                          LocationMatcher( filepath,  5, 14 ),
                          LocationMatcher( filepath,  5, 14 ) ),
            ChunkMatcher( '    ',
                          LocationMatcher( filepath,  6,  1 ),
                          LocationMatcher( filepath,  6,  3 ) ),
            ChunkMatcher( '        ',
                          LocationMatcher( filepath,  7,  1 ),
                          LocationMatcher( filepath,  7,  5 ) ),
            ChunkMatcher( '            ',
                          LocationMatcher( filepath,  8,  1 ),
                          LocationMatcher( filepath,  8,  7 ) ),
            ChunkMatcher( '            ',
                          LocationMatcher( filepath,  9,  1 ),
                          LocationMatcher( filepath,  9,  7 ) ),
            ChunkMatcher( '        ',
                          LocationMatcher( filepath, 10,  1 ),
                          LocationMatcher( filepath, 10,  5 ) ),
            ChunkMatcher( '    ',
                          LocationMatcher( filepath, 11,  1 ),
                          LocationMatcher( filepath, 11,  3 ) ),
            ChunkMatcher( ' ',
                          LocationMatcher( filepath, 11,  6 ),
                          LocationMatcher( filepath, 11,  6 ) ),
            ChunkMatcher( '    ',
                          LocationMatcher( filepath, 27,  1 ),
                          LocationMatcher( filepath, 27,  3 ) ),
            ChunkMatcher( '     ',
                          LocationMatcher( filepath, 28,  1 ),
                          LocationMatcher( filepath, 28,  4 ) ),
            ChunkMatcher( '     ',
                          LocationMatcher( filepath, 29,  1 ),
                          LocationMatcher( filepath, 29,  4 ) ),
            ChunkMatcher( '    ',
                          LocationMatcher( filepath, 30,  1 ),
                          LocationMatcher( filepath, 30,  3 ) ),
            ChunkMatcher( ' ',
                          LocationMatcher( filepath, 30, 17 ),
                          LocationMatcher( filepath, 30, 17 ) ),
          )
        } ) )
      } )
    }
  } )


@SharedYcmd
def Subcommands_Format_WholeFile_Tabs_test( app ):
  filepath = PathToTestFile( 'test.ts' )
  RunTest( app, {
    'description': 'Formatting is applied on the whole file '
                   'with tabs composed of 2 spaces',
    'request': {
      'command': 'Format',
      'filepath': filepath,
      'options': {
        'tab_size': 4,
        'insert_spaces': False
      }
    },
    'expect': {
      'response': requests.codes.ok,
      'data': has_entries( {
        'fixits': contains( has_entries( {
          'chunks': contains(
            ChunkMatcher( '\t',
                          LocationMatcher( filepath,  3,  1 ),
                          LocationMatcher( filepath,  3,  3 ) ),
            ChunkMatcher( '\t',
                          LocationMatcher( filepath,  4,  1 ),
                          LocationMatcher( filepath,  4,  3 ) ),
            ChunkMatcher( ' ',
                          LocationMatcher( filepath,  4, 14 ),
                          LocationMatcher( filepath,  4, 14 ) ),
            ChunkMatcher( '\t',
                          LocationMatcher( filepath,  5,  1 ),
                          LocationMatcher( filepath,  5,  3 ) ),
            ChunkMatcher( ' ',
                          LocationMatcher( filepath,  5, 14 ),
                          LocationMatcher( filepath,  5, 14 ) ),
            ChunkMatcher( '\t',
                          LocationMatcher( filepath,  6,  1 ),
                          LocationMatcher( filepath,  6,  3 ) ),
            ChunkMatcher( '\t\t',
                          LocationMatcher( filepath,  7,  1 ),
                          LocationMatcher( filepath,  7,  5 ) ),
            ChunkMatcher( '\t\t\t',
                          LocationMatcher( filepath,  8,  1 ),
                          LocationMatcher( filepath,  8,  7 ) ),
            ChunkMatcher( '\t\t\t',
                          LocationMatcher( filepath,  9,  1 ),
                          LocationMatcher( filepath,  9,  7 ) ),
            ChunkMatcher( '\t\t',
                          LocationMatcher( filepath, 10,  1 ),
                          LocationMatcher( filepath, 10,  5 ) ),
            ChunkMatcher( '\t',
                          LocationMatcher( filepath, 11,  1 ),
                          LocationMatcher( filepath, 11,  3 ) ),
            ChunkMatcher( ' ',
                          LocationMatcher( filepath, 11,  6 ),
                          LocationMatcher( filepath, 11,  6 ) ),
            ChunkMatcher( '\t',
                          LocationMatcher( filepath, 27,  1 ),
                          LocationMatcher( filepath, 27,  3 ) ),
            ChunkMatcher( '\t ',
                          LocationMatcher( filepath, 28,  1 ),
                          LocationMatcher( filepath, 28,  4 ) ),
            ChunkMatcher( '\t ',
                          LocationMatcher( filepath, 29,  1 ),
                          LocationMatcher( filepath, 29,  4 ) ),
            ChunkMatcher( '\t',
                          LocationMatcher( filepath, 30,  1 ),
                          LocationMatcher( filepath, 30,  3 ) ),
            ChunkMatcher( ' ',
                          LocationMatcher( filepath, 30, 17 ),
                          LocationMatcher( filepath, 30, 17 ) ),
          )
        } ) )
      } )
    }
  } )


@ExpectedFailure( 'formatRange not supported in typescript-language-server',
                  contains_string( '-32601' ) )
@SharedYcmd
def Subcommands_Format_Range_Spaces_test( app ):
  filepath = PathToTestFile( 'test.ts' )
  RunTest( app, {
    'description': 'Formatting is applied on some part of the file '
                   'with tabs composed of 4 spaces by default',
    'request': {
      'command': 'Format',
      'filepath': filepath,
      'range': {
        'start': {
          'line_num': 6,
          'column_num': 3,
        },
        'end': {
          'line_num': 11,
          'column_num': 6
        }
      },
      'options': {
        'tab_size': 4,
        'insert_spaces': True
      }
    },
    'expect': {
      'response': requests.codes.server_error,
      'data': has_entries( {
        'fixits': contains( has_entries( {
          'chunks': contains(
            ChunkMatcher( '    ',
                          LocationMatcher( filepath,  6,  1 ),
                          LocationMatcher( filepath,  6,  3 ) ),
            ChunkMatcher( '        ',
                          LocationMatcher( filepath,  7,  1 ),
                          LocationMatcher( filepath,  7,  5 ) ),
            ChunkMatcher( '            ',
                          LocationMatcher( filepath,  8,  1 ),
                          LocationMatcher( filepath,  8,  7 ) ),
            ChunkMatcher( '            ',
                          LocationMatcher( filepath,  9,  1 ),
                          LocationMatcher( filepath,  9,  7 ) ),
            ChunkMatcher( '        ',
                          LocationMatcher( filepath, 10,  1 ),
                          LocationMatcher( filepath, 10,  5 ) ),
            ChunkMatcher( '    ',
                          LocationMatcher( filepath, 11,  1 ),
                          LocationMatcher( filepath, 11,  3 ) ),
          )
        } ) )
      } )
    }
  } )


@ExpectedFailure( 'formatRange not supported in typescript-language-server',
                  contains_string( '-32601' ) )
@SharedYcmd
def Subcommands_Format_Range_Tabs_test( app ):
  filepath = PathToTestFile( 'test.ts' )
  RunTest( app, {
    'description': 'Formatting is applied on some part of the file '
                   'with tabs instead of spaces',
    'request': {
      'command': 'Format',
      'filepath': filepath,
      'range': {
        'start': {
          'line_num': 6,
          'column_num': 3,
        },
        'end': {
          'line_num': 11,
          'column_num': 6
        }
      },
      'options': {
        'tab_size': 4,
        'insert_spaces': False
      }
    },
    'expect': {
      'response': requests.codes.server_error,
      'data': has_entries( {
        'fixits': contains( has_entries( {
          'chunks': contains(
            ChunkMatcher( '\t',
                          LocationMatcher( filepath,  6,  1 ),
                          LocationMatcher( filepath,  6,  3 ) ),
            ChunkMatcher( '\t\t',
                          LocationMatcher( filepath,  7,  1 ),
                          LocationMatcher( filepath,  7,  5 ) ),
            ChunkMatcher( '\t\t\t',
                          LocationMatcher( filepath,  8,  1 ),
                          LocationMatcher( filepath,  8,  7 ) ),
            ChunkMatcher( '\t\t\t',
                          LocationMatcher( filepath,  9,  1 ),
                          LocationMatcher( filepath,  9,  7 ) ),
            ChunkMatcher( '\t\t',
                          LocationMatcher( filepath, 10,  1 ),
                          LocationMatcher( filepath, 10,  5 ) ),
            ChunkMatcher( '\t',
                          LocationMatcher( filepath, 11,  1 ),
                          LocationMatcher( filepath, 11,  3 ) ),
          )
        } ) )
      } )
    }
  } )


@SharedYcmd
def Subcommands_GetType_Basic_test( app ):
  RunTest( app, {
    'description': 'GetType works on a variable',
    'request': {
      'command': 'GetType',
      'line_num': 17,
      'column_num': 1,
      'filepath': PathToTestFile( 'test.ts' ),
    },
    'expect': {
      'response': requests.codes.ok,
      'data': MessageMatcher( 'var foo: Foo' )
    }
  } )


@SharedYcmd
def Subcommands_GetType_HasNoType_test( app ):
  RunTest( app, {
    'description': 'GetType returns an error on a keyword',
    'request': {
      'command': 'GetType',
      'line_num': 32,
      'column_num': 1,
      'filepath': PathToTestFile( 'test.ts' ),
    },
    'expect': {
      'response': requests.codes.internal_server_error,
      'data': ErrorMatcher( RuntimeError, 'No content available.' )
    }
  } )


@SharedYcmd
def Subcommands_GetDoc_Method_test( app ):
  RunTest( app, {
    'description': 'GetDoc on a method returns its docstring',
    'request': {
      'command': 'GetDoc',
      'line_num': 34,
      'column_num': 9,
      'filepath': PathToTestFile( 'test.ts' ),
    },
    'expect': {
      'response': requests.codes.ok,
      'data': has_entries( {
         'detailed_info': '(method) Bar.testMethod(): void\n\n'
                          'Method documentation'
      } )
    }
  } )


@SharedYcmd
def Subcommands_GetDoc_Class_test( app ):
  RunTest( app, {
    'description': 'GetDoc on a class returns its docstring',
    'request': {
      'command': 'GetDoc',
      'line_num': 37,
      'column_num': 2,
      'filepath': PathToTestFile( 'test.ts' ),
    },
    'expect': {
      'response': requests.codes.ok,
      'data': has_entries( {
         'detailed_info': 'class Bar\n\n'
                          'Class documentation\n\n'
                          'Multi-line'
      } )
    }
  } )


@SharedYcmd
def Subcommands_GetDoc_Class_Unicode_test( app ):
  RunTest( app, {
    'description': 'GetDoc works with Unicode characters',
    'request': {
      'command': 'GetDoc',
      'line_num': 35,
      'column_num': 12,
      'filepath': PathToTestFile( 'unicode.ts' ),
    },
    'expect': {
      'response': requests.codes.ok,
      'data': has_entries( {
         'detailed_info': 'class Båøz\n\n'
                          'Test unicøde st††††',
      } )
    }
  } )


@SharedYcmd
def Subcommands_GetDoc_NoDocstring_test( app ):
  RunTest( app, {
    'description': 'GetDoc returns an error on a keyword',
    'request': {
      'command': 'GetType',
      'line_num': 32,
      'column_num': 1,
      'filepath': PathToTestFile( 'test.ts' ),
    },
    'expect': {
      'response': requests.codes.internal_server_error,
      'data': ErrorMatcher( RuntimeError, 'No content available.' )
    }
  } )


@SharedYcmd
def Subcommands_GoToReferences_test( app ):
  RunTest( app, {
    'description': 'GoToReferences works',
    'request': {
      'command': 'GoToReferences',
      'line_num': 33,
      'column_num': 6,
      'filepath': PathToTestFile( 'test.ts' ),
    },
    'expect': {
      'response': requests.codes.ok,
      'data': contains_inanyorder(
        has_entries( { 'description': 'var bar = new Bar();',
                       'line_num'   : 33,
                       'column_num' : 5,
                       'filepath'   : PathToTestFile( 'test.ts' ) } ),
        has_entries( { 'description': 'bar.testMethod();',
                       'line_num'   : 34,
                       'column_num' : 1,
                       'filepath'   : PathToTestFile( 'test.ts' ) } ),
        has_entries( { 'description': 'bar.nonExistingMethod();',
                       'line_num'   : 35,
                       'column_num' : 1,
                       'filepath'   : PathToTestFile( 'test.ts' ) } ),
        has_entries( { 'description': 'var bar = new Bar();',
                       'line_num'   : 1,
                       'column_num' : 5,
                       'filepath'   : PathToTestFile( 'file3.ts' ) } ),
        has_entries( { 'description': 'bar.testMethod();',
                       'line_num'   : 2,
                       'column_num' : 1,
                       'filepath'   : PathToTestFile( 'file3.ts' ) } )
      )
    }
  } )


@SharedYcmd
def Subcommands_GoToReferences_Unicode_test( app ):
  RunTest( app, {
    'description': 'GoToReferences works with Unicode characters',
    'request': {
      'command': 'GoToReferences',
      'line_num': 14,
      'column_num': 3,
      'filepath': PathToTestFile( 'unicode.ts' ),
    },
    'expect': {
      'response': requests.codes.ok,
      'data': contains_inanyorder(
        has_entries( { 'description': '  å: number;',
                       'line_num'   : 14,
                       'column_num' : 3,
                       'filepath'   : PathToTestFile( 'unicode.ts' ) } ),
        has_entries( { 'description': 'var baz = new Bår(); baz.å;',
                       'line_num'   : 20,
                       'column_num' : 27,
                       'filepath'   : PathToTestFile( 'unicode.ts' ) } ),
        has_entries( { 'description': 'baz.å;',
                       'line_num'   : 23,
                       'column_num' : 5,
                       'filepath'   : PathToTestFile( 'unicode.ts' ) } ),
        has_entries( { 'description': 'føø_long_long.å;',
                       'line_num'   : 27,
                       'column_num' : 17,
                       'filepath'   : PathToTestFile( 'unicode.ts' ) } )
      )
    }
  } )


@SharedYcmd
def Subcommands_GoTo_Basic( app, goto_command ):
  RunTest( app, {
    'description': goto_command + ' works within file',
    'request': {
      'command': goto_command,
      'line_num': 34,
      'column_num': 8,
      'filepath': PathToTestFile( 'test.ts' ),
    },
    'expect': {
      'response': requests.codes.ok,
      'data': LocationMatcher( PathToTestFile( 'test.ts' ), 30, 3 )
    }
  } )


def Subcommands_GoTo_Basic_test():
  for command in [ 'GoTo', 'GoToDefinition', 'GoToDeclaration' ]:
    yield Subcommands_GoTo_Basic, command


@SharedYcmd
def Subcommands_GoTo_Unicode( app, goto_command ):
  RunTest( app, {
    'description': goto_command + ' works with Unicode characters',
    'request': {
      'command': goto_command,
      'line_num': 28,
      'column_num': 19,
      'filepath': PathToTestFile( 'unicode.ts' ),
    },
    'expect': {
      'response': requests.codes.ok,
      'data': LocationMatcher( PathToTestFile( 'unicode.ts' ), 15, 3 )
    }
  } )


def Subcommands_GoTo_Unicode_test():
  for command in [ 'GoTo', 'GoToDefinition', 'GoToDeclaration' ]:
    yield Subcommands_GoTo_Unicode, command


@SharedYcmd
def Subcommands_GoTo_Fail( app, goto_command ):
  RunTest( app, {
    'description': goto_command + ' fails on non-existing method',
    'request': {
      'command': goto_command,
      'line_num': 35,
      'column_num': 6,
      'filepath': PathToTestFile( 'test.ts' ),
    },
    'expect': {
      'response': requests.codes.internal_server_error,
      'data': ErrorMatcher( RuntimeError, 'Cannot jump to location' )
    }
  } )


def Subcommands_GoTo_Fail_test():
  for command in [ 'GoTo', 'GoToDefinition', 'GoToDeclaration' ]:
    yield Subcommands_GoTo_Fail, command


@SharedYcmd
def Subcommands_GoToType_test( app ):
  RunTest( app, {
    'description': 'GoToType works',
    'request': {
      'command': 'GoToType',
      'line_num': 14,
      'column_num': 6,
      'filepath': PathToTestFile( 'test.ts' ),
    },
    'expect': {
      'response': requests.codes.ok,
      'data': LocationMatcher( PathToTestFile( 'test.ts' ), 2, 7 )
    }
  } )


@SharedYcmd
def Subcommands_GoToType_Fail_test( app ):
  RunTest( app, {
    'description': 'GoToType fails outside the buffer',
    'request': {
      'command': 'GoToType',
      'line_num': 39,
      'column_num': 8,
      'filepath': PathToTestFile( 'test.ts' ),
    },
    'expect': {
      'response': requests.codes.internal_server_error,
      'data': ErrorMatcher( RuntimeError, 'Cannot jump to location' )
    }
  } )


@SharedYcmd
def Subcommands_FixIt_test( app ):
  filepath = PathToTestFile( 'test.ts' )
  contents = ReadFile( filepath )
  line_sep = os.linesep
  WaitForDiagnosticsToBeReady( app, filepath, contents, 'typescript' )
  RunTest( app, {
    'description': 'FixIt works on a non-existing method',
    'request': {
      'command': 'FixIt',
      'line_num': 35,
      'column_num': 12,
      'filepath': filepath,
    },
    'resolve_fixits': True,
    'expect': {
      'response': requests.codes.ok,
      'data': contains_inanyorder(
        has_entries( {
          'fixits': contains( has_entries( {
            'chunks': contains( has_entries( {
              'range': RangeMatcher( filepath, ( 25, 12 ), ( 25, 12 ) ),
              'replacement_text':
                    "{0}    nonExistingMethod() ".format( line_sep ) +
                    "{{{0}        throw new".format( line_sep ) +
                    " Error(\"Method not implemented." +
                    "\");{0}    }}".format( line_sep )
            } ) ),
            'location': LocationMatcher( filepath, 35, 12 ),
            'resolve': False,
            'text': "Declare method 'nonExistingMethod'"
          } ) )
        } ),
        has_entries( {
          'fixits': contains( has_entries( {
            'chunks': contains( has_entries( {
              'range': RangeMatcher( filepath, ( 25, 12 ), ( 25, 12 ) ),
              'replacement_text':
                  "{}    nonExistingMethod: any;".format( line_sep )
            } ) ),
            'location': LocationMatcher( filepath, 35, 12 ),
            'resolve': False,
            'text': "Declare property 'nonExistingMethod'"
          } ) )
        } ),
        has_entries( {
          'fixits': contains( has_entries( {
            'chunks': contains( has_entries( {
              'range': RangeMatcher( filepath, ( 25, 12 ), ( 25, 12 ) ),
              'replacement_text': "{}    [x: string]: any;".format( line_sep )
            } ) ),
            'location': LocationMatcher( filepath, 35, 12 ),
            'resolve': False,
            'text': "Add index signature for property 'nonExistingMethod'"
          } ) )
        } )
      )
    }
  } )



@SharedYcmd
def Subcommands_OrganizeImports_test( app ):
  filepath = PathToTestFile( 'imports.ts' )
  RunTest( app, {
    'description': 'OrganizeImports removes unused imports, '
                   'coalesces imports from the same module, and sorts them',
    'request': {
      'command': 'OrganizeImports',
      'filepath': filepath,
    },
    'expect': {
      'response': requests.codes.ok,
      'data': has_entries( {
        'fixits': contains( has_entries( {
          'chunks': contains(
            ChunkMatcher(
              matches_regexp(
                'import \\* as lib from "library";\r?\n'
                'import func, { func1, func2 } from "library";\r?\n' ),
              LocationMatcher( filepath,  1, 1 ),
              LocationMatcher( filepath,  2, 1 ) ),
            ChunkMatcher(
              '',
              LocationMatcher( filepath,  5, 1 ),
              LocationMatcher( filepath,  6, 1 ) ),
            ChunkMatcher(
              '',
              LocationMatcher( filepath,  9, 1 ),
              LocationMatcher( filepath, 10, 1 ) ),
          )
        } ) )
      } )
    }
  } )


@SharedYcmd
def Subcommands_RefactorRename_Missing_test( app ):
  RunTest( app, {
    'description': 'RefactorRename requires a parameter',
    'request': {
      'command': 'RefactorRename',
      'line_num': 30,
      'column_num': 6,
      'filepath': PathToTestFile( 'test.ts' ),
    },
    'expect': {
      'response': requests.codes.internal_server_error,
      'data': ErrorMatcher( ValueError,
                            'Please specify a new name to rename it to.\n'
                            'Usage: RefactorRename <new name>' )
    }
  } )


@SharedYcmd
def Subcommands_RefactorRename_NotPossible_test( app ):
  RunTest( app, {
    'description': 'RefactorRename cannot rename a non-existing method',
    'request': {
      'command': 'RefactorRename',
      'arguments': [ 'whatever' ],
      'line_num': 35,
      'column_num': 5,
      'filepath': PathToTestFile( 'test.ts' ),
    },
    'expect': {
      'response': requests.codes.internal_server_error,
      'data': ErrorMatcher( RuntimeError,
                            'Cannot rename the symbol under cursor.' )
    }
  } )


@SharedYcmd
def Subcommands_RefactorRename_Simple_test( app ):
  RunTest( app, {
    'description': 'RefactorRename works on a class name',
    'request': {
      'command': 'RefactorRename',
      'arguments': [ 'test' ],
      'line_num': 2,
      'column_num': 8,
      'filepath': PathToTestFile( 'test.ts' ),
    },
    'expect': {
      'response': requests.codes.ok,
      'data': has_entries( {
        'fixits': contains( has_entries( {
          'chunks': contains_inanyorder(
            ChunkMatcher(
              'test',
              LocationMatcher( PathToTestFile( 'test.ts' ), 14, 15 ),
              LocationMatcher( PathToTestFile( 'test.ts' ), 14, 18 ) ),
            ChunkMatcher(
              'test',
              LocationMatcher( PathToTestFile( 'test.ts' ), 2, 7 ),
              LocationMatcher( PathToTestFile( 'test.ts' ), 2, 10 ) ),
          ),
          'location': LocationMatcher( PathToTestFile( 'test.ts' ), 2, 8 )
        } ) )
      } )
    }
  } )


@SharedYcmd
def Subcommands_RefactorRename_MultipleFiles_test( app ):
  RunTest( app, {
    'description': 'RefactorRename works across files',
    'request': {
      'command': 'RefactorRename',
      'arguments': [ 'this-is-a-longer-string' ],
      'line_num': 25,
      'column_num': 9,
      'filepath': PathToTestFile( 'test.ts' ),
    },
    'expect': {
      'response': requests.codes.ok,
      'data': has_entries( {
        'fixits': contains( has_entries( {
          'chunks': contains_inanyorder(
            ChunkMatcher(
              'this-is-a-longer-string',
              LocationMatcher( PathToTestFile( 'test.ts' ), 25, 7 ),
              LocationMatcher( PathToTestFile( 'test.ts' ), 25, 10 ) ),
            ChunkMatcher(
              'this-is-a-longer-string',
              LocationMatcher( PathToTestFile( 'test.ts' ), 33, 15 ),
              LocationMatcher( PathToTestFile( 'test.ts' ), 33, 18 ) ),
            ChunkMatcher(
              'this-is-a-longer-string',
              LocationMatcher( PathToTestFile( 'test.ts' ), 37, 1 ),
              LocationMatcher( PathToTestFile( 'test.ts' ), 37, 4 ) ),
            ChunkMatcher(
              'this-is-a-longer-string',
              LocationMatcher( PathToTestFile( 'file2.ts' ), 1, 5 ),
              LocationMatcher( PathToTestFile( 'file2.ts' ), 1, 8 ) ),
            ChunkMatcher(
              'this-is-a-longer-string',
              LocationMatcher( PathToTestFile( 'file3.ts' ), 1, 15 ),
              LocationMatcher( PathToTestFile( 'file3.ts' ), 1, 18 ) ),
            ChunkMatcher(
              'this-is-a-longer-string',
              LocationMatcher( PathToTestFile( 'test.tsx' ), 10, 8 ),
              LocationMatcher( PathToTestFile( 'test.tsx' ), 10, 11 ) ),
          ),
          'location': LocationMatcher( PathToTestFile( 'test.ts' ), 25, 9 )
        } ) )
      } )
    }
  } )


@SharedYcmd
def Subcommands_RefactorRename_SimpleUnicode_test( app ):
  RunTest( app, {
    'description': 'RefactorRename works with Unicode characters',
    'request': {
      'command': 'RefactorRename',
      'arguments': [ 'ø' ],
      'line_num': 14,
      'column_num': 3,
      'filepath': PathToTestFile( 'unicode.ts' ),
    },
    'expect': {
      'response': requests.codes.ok,
      'data': has_entries( {
        'fixits': contains( has_entries( {
          'chunks': contains_inanyorder(
            ChunkMatcher(
              'ø',
              LocationMatcher( PathToTestFile( 'unicode.ts' ), 14, 3 ),
              LocationMatcher( PathToTestFile( 'unicode.ts' ), 14, 5 ) ),
            ChunkMatcher(
              'ø',
              LocationMatcher( PathToTestFile( 'unicode.ts' ), 20, 27 ),
              LocationMatcher( PathToTestFile( 'unicode.ts' ), 20, 29 ) ),
            ChunkMatcher(
              'ø',
              LocationMatcher( PathToTestFile( 'unicode.ts' ), 23, 5 ),
              LocationMatcher( PathToTestFile( 'unicode.ts' ), 23, 7 ) ),
            ChunkMatcher(
              'ø',
              LocationMatcher( PathToTestFile( 'unicode.ts' ), 27, 17 ),
              LocationMatcher( PathToTestFile( 'unicode.ts' ), 27, 19 ) ),
          ),
          'location': LocationMatcher( PathToTestFile( 'unicode.ts' ), 14, 3 )
        } ) )
      } )
    }
  } )


@IsolatedYcmd()
@patch( 'ycmd.utils.WaitUntilProcessIsTerminated',
        MockProcessTerminationTimingOut )
def Subcommands_StopServer_Timeout_test( app ):
  app.post_json( '/event_notification',
                 BuildRequest(
                   filepath = PathToTestFile( 'test.ts' ),
                   event_name = 'FileReadyToParse',
                   filetype = 'typescript' ) )
  WaitUntilCompleterServerReady( app, 'typescript' )

  app.post_json(
    '/run_completer_command',
    BuildRequest(
      filetype = 'typescript',
      command_arguments = [ 'StopServer' ]
    )
  )

  request_data = BuildRequest( filetype = 'typescript' )
  assert_that( app.post_json( '/debug_info', request_data ).json,
               has_entry(
                 'completer',
                 has_entry( 'servers', contains(
                   has_entry( 'is_running', False )
                 ) )
               ) )
