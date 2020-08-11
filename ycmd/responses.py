# Copyright (C) 2013-2020 ycmd contributors
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
from ycmd.utils import ProcessIsRunning
from subprocess import Popen
from typing import Any, Dict, List, Optional, Union


YCM_EXTRA_CONF_FILENAME = '.ycm_extra_conf.py'

CONFIRM_CONF_FILE_MESSAGE = ( 'Found {0}. Load? \n\n(Question can be turned '
                              'off with options, see YCM docs)' )

NO_EXTRA_CONF_FILENAME_MESSAGE = ( f'No { YCM_EXTRA_CONF_FILENAME } file '
  'detected, so no compile flags are available. Thus no semantic support for '
  'C/C++/ObjC/ObjC++. Go READ THE ' 'DOCS *NOW*, DON\'T file a bug report.' )

NO_DIAGNOSTIC_SUPPORT_MESSAGE = ( 'YCM has no diagnostics support for this '
  'filetype; refer to Syntastic docs if using Syntastic.' )

EMPTY_SIGNATURE_INFO = {
  'activeSignature': 0,
  'activeParameter': 0,
  'signatures': [],
}


class SignatureHelpAvailalability:
  AVAILABLE = 'YES'
  NOT_AVAILABLE = 'NO'
  PENDING = 'PENDING'


class ServerError( Exception ):
  def __init__( self, message: str ) -> None:
    super().__init__( message )


class UnknownExtraConf( ServerError ):
  def __init__( self, extra_conf_file: str ) -> None:
    message = CONFIRM_CONF_FILE_MESSAGE.format( extra_conf_file )
    super().__init__( message )
    self.extra_conf_file = extra_conf_file


class NoExtraConfDetected( ServerError ):
  def __init__( self ) -> None:
    super().__init__( NO_EXTRA_CONF_FILENAME_MESSAGE )


class NoDiagnosticSupport( ServerError ):
  def __init__( self ) -> None:
    super().__init__( NO_DIAGNOSTIC_SUPPORT_MESSAGE )


class Location:
  """Source code location for a diagnostic or FixIt (aka Refactor)."""

  def __init__( self, line: int, column: int, filename: str ) -> None:
    """Line is 1-based line, column is 1-based column byte offset, filename is
    absolute path of the file"""
    self.line_number_ = line
    self.column_number_ = column
    if filename:
      self.filename_ = os.path.abspath( filename )
    else:
      # When the filename passed (e.g. by a server) can't be recognized or
      # parsed, we send an empty filename. This at least allows the client to
      # know there _is_ a reference, but not exactly where it is. This can
      # happen with the Java completer which sometimes returns references using
      # a custom/undocumented URI scheme. Typically, such URIs point to .class
      # files or other binary data which clients can't display anyway.
      # FIXME: Sending a location with an empty filename could be considered a
      # strict breach of our own protocol. Perhaps completers should be required
      # to simply skip such a location.
      self.filename_ = filename


class Range:
  """Source code range relating to a diagnostic or FixIt (aka Refactor)."""

  def __init__( self, start: Location, end: Location ) -> None:
    "start of type Location, end of type Location"""
    self.start_ = start
    self.end_ = end


# column_num is a byte offset
def BuildGoToResponse( filepath: str, line_num: int, column_num: int, description: Optional[str] = None ) -> Dict[str, Union[int, str]]:
  return BuildGoToResponseFromLocation(
    Location( line = line_num,
              column = column_num,
              filename = filepath ),
    description )


def BuildGoToResponseFromLocation( location: Location, description: Optional[str] = None ) -> Dict[str, Union[int, str]]:
  """Build a GoTo response from a responses.Location object."""
  response = BuildLocationData( location )
  if description:
    response[ 'description' ] = description
  return response


def BuildDescriptionOnlyGoToResponse( text ):
  return {
    'description': text,
  }


def BuildDisplayMessageResponse( text: str ) -> Dict[str, str]:
  return {
    'message': text
  }


def BuildDetailedInfoResponse( text: str ) -> Dict[str, str]:
  """ Returns the response object for displaying detailed information about types
  and usage, such as within a preview window"""
  return {
    'detailed_info': text
  }


def BuildCompletionData( insertion_text: str,
                         extra_menu_info: Optional[str] = None,
                         detailed_info: Optional[str] = None,
                         menu_text: Optional[str] = None,
                         kind: Optional[str] = None,
                         extra_data: Optional[Any] = None ) -> Dict[str, Any]:
  completion_data = {
    'insertion_text': insertion_text
  }

  if extra_menu_info:
    completion_data[ 'extra_menu_info' ] = extra_menu_info
  if menu_text:
    completion_data[ 'menu_text' ] = menu_text
  if detailed_info:
    completion_data[ 'detailed_info' ] = detailed_info
  if kind:
    completion_data[ 'kind' ] = kind
  if extra_data:
    completion_data[ 'extra_data' ] = extra_data
  return completion_data


# start_column is a byte offset
def BuildCompletionResponse( completions: Union[List[Dict[str, Union[str, Dict[str, Dict[str, Union[int, str]]]]]], List[Dict[str, Union[str, Dict[str, List[Dict[str, Union[Dict[str, Union[int, str]], List[Dict[str, Union[str, Dict[str, Dict[str, Union[int, str]]]]]], str, bool]]]]]]], List[Dict[str, str]], List[Union[Dict[str, Union[str, Dict[str, str]]], Dict[str, str]]]],
                             start_column: int,
                             errors: Optional[Union[List[Dict[str, Union[RuntimeError, str]]], List[Dict[str, Union[ValueError, str]]]]] = None ) -> Dict[str, Any]:
  return {
    'completions': completions,
    'completion_start_column': start_column,
    'errors': errors if errors else [],
  }


def BuildSignatureHelpResponse( signature_info: Optional[Union[Dict[str, int], Dict[str, Union[int, List[Dict[str, Union[Dict[str, str], str, List[Dict[str, List[int]]]]]]]], Dict[str, Union[List[Dict[str, str]], int]], Dict[str, Union[List[Dict[str, Union[str, List[Dict[str, List[int]]]]]], int]]]], errors: Optional[List[Dict[str, Union[RuntimeError, str]]]] = None ) -> Dict[str, Union[Dict[str, Union[List[Dict[str, str]], int]], Dict[str, int], List[Dict[str, Union[RuntimeError, str]]], Dict[str, Union[int, List[Dict[str, Union[Dict[str, str], str, List[Dict[str, List[int]]]]]]]], Dict[str, Union[List[Dict[str, Union[str, List[Dict[str, List[int]]]]]], int]]]]:
  return {
    'signature_help':
      signature_info if signature_info else EMPTY_SIGNATURE_INFO,
    'errors': errors if errors else [],
  }


# location.column_number_ is a byte offset
def BuildLocationData( location: Union[Location, Location] ) -> Dict[str, Union[int, str]]:
  return {
    'line_num': location.line_number_,
    'column_num': location.column_number_,
    'filepath': ( os.path.normpath( location.filename_ )
                  if location.filename_ else '' ),
  }


def BuildRangeData( source_range: Union[Range, Range] ) -> Dict[str, Dict[str, Union[int, str]]]:
  return {
    'start': BuildLocationData( source_range.start_ ),
    'end': BuildLocationData( source_range.end_ ),
  }


class FixItChunk:
  """An individual replacement within a FixIt (aka Refactor)"""

  def __init__( self, replacement_text: str, range: Range ) -> None:
    """replacement_text of type string, range of type Range"""
    self.replacement_text = replacement_text
    self.range = range


class FixIt:
  """A set of replacements (of type FixItChunk) to be applied to fix a single
  diagnostic. This can be used for any type of refactoring command, not just
  quick fixes. The individual chunks may span multiple files.

  NOTE: All offsets supplied in both |location| and (the members of) |chunks|
  must be byte offsets into the UTF-8 encoded version of the appropriate
  buffer.
  """
  class Kind:
    """These are LSP kinds that we use outside of LSP completers."""
    REFACTOR = 'refactor'


  def __init__( self, location: Location, chunks: List[FixItChunk], text: Optional[str] = '', kind: Optional[str] = None ) -> None:
    """location of type Location, chunks of type list<FixItChunk>"""
    self.location = location
    self.chunks = chunks
    self.text = text
    self.kind = kind


class Diagnostic:
  def __init__( self,
                ranges: List[Range],
                location: Location,
                location_extent: Range,
                text: str,
                kind: str,
                fixits: List[FixIt] = [] ) -> None:
    self.ranges_ = ranges
    self.location_ = location
    self.location_extent_ = location_extent
    self.text_ = text
    self.kind_ = kind
    self.fixits_ = fixits


class UnresolvedFixIt:
  def __init__( self, command: Dict[str, Union[int, List[Dict[str, Union[Dict[str, Dict[str, int]], str]]], str]], text: str, kind: Optional[str] = None ) -> None:
    self.command = command
    self.text = text
    self.resolve = True
    self.kind = kind


def BuildDiagnosticData( diagnostic: Union[Diagnostic, Diagnostic] ) -> Dict[str, Union[List[Dict[str, Dict[str, Union[int, str]]]], Dict[str, Union[int, str]], Dict[str, Dict[str, Union[int, str]]], str, bool]]:
  kind = ( diagnostic.kind_.name if hasattr( diagnostic.kind_, 'name' )
           else diagnostic.kind_ )

  return {
    'ranges': [ BuildRangeData( x ) for x in diagnostic.ranges_ ],
    'location': BuildLocationData( diagnostic.location_ ),
    'location_extent': BuildRangeData( diagnostic.location_extent_ ),
    'text': diagnostic.text_,
    'kind': kind,
    'fixit_available': len( diagnostic.fixits_ ) > 0,
  }


def BuildDiagnosticResponse( diagnostics: Union[List[Diagnostic], List[Diagnostic]],
                             filename: str,
                             max_diagnostics_to_display: int ) -> Union[List[Dict[str, Union[List[Dict[str, Dict[str, Union[int, str]]]], Dict[str, Union[int, str]], Dict[str, Dict[str, Union[int, str]]], str, bool]]], List[Dict[str, Union[Dict[str, Union[int, str]], Dict[str, Dict[str, Union[int, str]]], str, bool]]], List[Union[Dict[str, Union[List[Dict[str, Dict[str, Union[int, str]]]], Dict[str, Union[int, str]], Dict[str, Dict[str, Union[int, str]]], str, bool]], Dict[str, Union[Dict[str, Union[int, str]], Dict[str, Dict[str, Union[int, str]]], str, bool]]]]]:
  if ( max_diagnostics_to_display and
       len( diagnostics ) > max_diagnostics_to_display ):
    diagnostics = diagnostics[ : max_diagnostics_to_display ]
    location = Location( 1, 1, filename )
    location_extent = Range( location, location )
    diagnostics.append( Diagnostic(
      [ location_extent ],
      location,
      location_extent,
      'Maximum number of diagnostics exceeded.',
      'ERROR'
    ) )
  return [ BuildDiagnosticData( diagnostic ) for diagnostic in diagnostics ]


def BuildFixItResponse( fixits: Union[List[FixIt], List[UnresolvedFixIt], List[FixIt], List[Union[FixIt, UnresolvedFixIt]]] ) -> Dict[str, Any]:
  """Build a response from a list of FixIt (aka Refactor) objects. This response
  can be used to apply arbitrary changes to arbitrary files and is suitable for
  both quick fix and refactor operations"""

  def BuildFixitChunkData( chunk ):
    return {
      'replacement_text': chunk.replacement_text,
      'range': BuildRangeData( chunk.range ),
    }

  def BuildFixItData( fixit ):
    if hasattr( fixit, 'resolve' ):
      result = {
        'command': fixit.command,
        'text': fixit.text,
        'kind': fixit.kind,
        'resolve': fixit.resolve
      }
    else:
      result = {
        'location': BuildLocationData( fixit.location ),
        'chunks' : [ BuildFixitChunkData( x ) for x in fixit.chunks ],
        'text': fixit.text,
        'kind': fixit.kind,
        'resolve': False
      }

    if result[ 'kind' ] is None:
      result.pop( 'kind' )

    return result

  return {
    'fixits' : [ BuildFixItData( x ) for x in fixits ]
  }


def BuildExceptionResponse( exception: Any, traceback: Optional[str] ) -> Dict[str, Any]:
  return {
    'exception': exception,
    'message': str( exception ),
    'traceback': traceback
  }


class DebugInfoItem:

  def __init__( self, key: str, value: Optional[Union[List[str], str, bool]] ) -> None:
    self.key = key
    self.value = value


class DebugInfoServer:
  """Store debugging information on a server:
  - name: the server name;
  - is_running: True if the server process is alive, False otherwise;
  - executable: path of the executable used to start the server;
  - address: if applicable, the address on which the server is listening. None
    otherwise;
  - port: if applicable, the port on which the server is listening. None
    otherwise;
  - pid: the process identifier of the server. None if the server is not
    running;
  - logfiles: a list of logging files used by the server;
  - extras: a list of DebugInfoItem objects for additional information on the
    server."""

  def __init__( self,
                name: str,
                handle: Optional[Popen],
                executable: Union[str, List[Optional[str]], List[str]],
                address: Optional[str] = None,
                port: Optional[int] = None,
                logfiles: Union[List[None], List[str]] = [],
                extras: List[DebugInfoItem] = [] ) -> None:
    self.name = name
    self.is_running = ProcessIsRunning( handle )
    self.executable = executable
    self.address = address
    self.port = port
    self.pid = handle.pid if self.is_running else None
    # Remove undefined logfiles from the list.
    self.logfiles = [ logfile for logfile in logfiles if logfile ]
    self.extras = extras


def BuildDebugInfoResponse( name: str, servers: List[DebugInfoServer] = [], items: List[DebugInfoItem] = [] ) -> Dict[str, Any]:
  """Build a response containing debugging information on a semantic completer:
  - name: the completer name;
  - servers: a list of DebugInfoServer objects representing the servers used by
    the completer;
  - items: a list of DebugInfoItem objects for additional information
    on the completer."""

  def BuildItemData( item ):
    return {
      'key': item.key,
      'value': item.value
    }


  def BuildServerData( server ):
    return {
      'name': server.name,
      'is_running': server.is_running,
      'executable': server.executable,
      'address': server.address,
      'port': server.port,
      'pid': server.pid,
      'logfiles': server.logfiles,
      'extras': [ BuildItemData( item ) for item in server.extras ]
    }


  return {
    'name': name,
    'servers': [ BuildServerData( server ) for server in servers ],
    'items': [ BuildItemData( item ) for item in items ]
  }


def BuildSignatureHelpAvailableResponse( value: str ) -> Dict[str, str]:
  return { 'available': value }
