#!/usr/bin/env python

import re
import swift_ycm_core
from ycmd import responses
from ycmd import extra_conf_store
from ycmd.utils import ToCppStringCompatible
from ycmd.responses import NoExtraConfDetected
from ycmd.completers.completer import Completer
from collections import namedtuple, defaultdict

SWIFT_FILETYPES = set( [ 'swift' ] )
INVALID_FILE_MESSAGE = 'File is invalid.'
NO_DIAGNOSTIC_MESSAGE = 'No diagnostic for current line!'
NO_COMPLETIONS_MESSAGE = 'No completions found; errors in the file?'


class FlagStore( object ):
  def __init__( self ):
    self.flags_for_file = {}
    self.no_extra_conf_file_warning_posted = False

  def PassFlags( self, compiler, filename ):
    if filename in self.flags_for_file:
      return

    module = extra_conf_store.ModuleForSourceFile( filename )
    if not module:
      if not self.no_extra_conf_file_warning_posted:
        self.no_extra_conf_file_warning_posted = True
        raise NoExtraConfDetected
      return

    results = module.FlagsForFile( filename )
    if not results or not results.get( 'flags_ready', True ):
      return

    flags = list( results[ 'flags' ] )
    if not flags:
      return

    if results[ 'do_cache' ]:
      self.flags_for_file[ filename ] = flags

    import_search_paths = []
    framework_search_paths = []

    for i in range( 0, len(flags), 2 ):
      flag = flags[ i ]
      if flag == '-I':
        import_search_paths.append( flags[ i + 1 ] )
      if flag == '-F':
        framework_search_paths.append( flags[ i + 1 ] )

    compiler.import_search_paths = import_search_paths
    compiler.framework_search_paths = framework_search_paths


class SwiftCompleter( Completer ):
  def __init__( self, user_options ):
    super( SwiftCompleter, self ).__init__( user_options )
    self._max_diagnostics_to_display = user_options[
      'max_diagnostics_to_display' ]
    self._compiler = swift_ycm_core.Compiler()
    self._flag_store = FlagStore()
    self._diagnostic_store = None


  def SupportedFiletypes( self ):
    return SWIFT_FILETYPES


  def CurrentTriggerKind( self, request_data ):
    if not self.prepared_triggers:
      return "COMPLETION"

    current_line = request_data[ 'line_value' ]
    start_column = request_data[ 'start_column' ] - 1
    current_column = request_data[ 'column_num' ] - 1
    filetype = self._CurrentFiletype( request_data[ 'filetypes' ] )

    trigger = self.prepared_triggers.MatchingTriggerForFiletype(
        current_line,
        start_column,
        current_column,
        filetype )

    if trigger is not None and trigger.pattern != re.escape( '.' ):
      if current_column == start_column:
        return "HINT"
      return "AFTER_HINT"

    return "COMPLETION"


  def ShouldUseNowInner( self, request_data ):
    current_trigger_kind = self.CurrentTriggerKind( request_data )
    if current_trigger_kind == "AFTER_HINT":
      return False

    return super( SwiftCompleter, self ).ShouldUseNowInner( request_data )


  def ComputeCandidatesInner( self, request_data ):
    filename = request_data[ 'filepath' ]
    if not filename:
      return

    filename = ToCppStringCompatible( filename )
    contents = request_data[ 'file_data' ][ filename ][ 'contents' ]

    self._flag_store.PassFlags( self._compiler, filename )

    if self.CurrentTriggerKind( request_data ) == "HINT":
      completions = self._compiler.hints(
          ToCppStringCompatible( contents ),
          request_data[ 'line_num' ],
          request_data[ 'start_column' ] )
      return [ ConvertCompletionData( x ) for x in completions ]

    completions = self._compiler.completions(
        ToCppStringCompatible( contents ),
        request_data[ 'line_num' ],
        request_data[ 'start_column' ] )
    if not completions:
      raise RuntimeError( NO_COMPLETIONS_MESSAGE )
    return [ ConvertCompletionData( x ) for x in completions ]


  def OnFileReadyToParse( self, request_data ):
    filename = request_data[ 'filepath' ]
    if not filename:
      raise ValueError( INVALID_FILE_MESSAGE )
    filename = ToCppStringCompatible( filename )
    contents = request_data[ 'file_data' ][ filename ][ 'contents' ]

    self._flag_store.PassFlags( self._compiler, filename )

    diagnostics = self._compiler.diagnostics(
        ToCppStringCompatible( contents ),
        filename )

    self._diagnostic_store = DiagnosticsToDiagStructure( diagnostics )
    return [ responses.BuildDiagnosticData( x ) for x in
             diagnostics[ : self._max_diagnostics_to_display ] ]


  def GetDetailedDiagnostic( self, request_data ):
    current_line = request_data[ 'line_num' ]
    current_column = request_data[ 'column_num' ]
    current_file = request_data[ 'filepath' ]

    if not current_file:
      raise ValueError( INVALID_FILE_MESSAGE )

    if not self._diagnostic_store:
      raise ValueError( NO_DIAGNOSTIC_MESSAGE )

    diagnostics = self._diagnostic_store[ current_file ][ current_line ]
    if not diagnostics:
      raise ValueError( NO_DIAGNOSTIC_MESSAGE )

    closest_diagnostic = None
    distance_to_closest_diagnostic = 999

    for diagnostic in diagnostics:
      distance = abs( current_column - diagnostic.location_.column_number_ )
      if distance < distance_to_closest_diagnostic:
        distance_to_closest_diagnostic = distance
        closest_diagnostic = diagnostic

    return responses.BuildDisplayMessageResponse(
      closest_diagnostic.long_formatted_text_ )


  def _FixIt( self, request_data ):
    line = request_data[ 'line_num' ]
    filename = request_data[ 'filepath' ]

    if not filename:
      raise ValueError( INVALID_FILE_MESSAGE )

    diagnostics = self._diagnostic_store[ filename ][ line ]
    if not diagnostics:
      raise ValueError( NO_DIAGNOSTIC_MESSAGE )

    fixit = namedtuple( 'fixit', 'chunks location' )
    fixits = [ fixit(chunks = x.fixits_, location = x.location_ ) for x in
               diagnostics ]

    return responses.BuildFixItResponse( fixits )

  def GetSubcommandsMap( self ):
    return { 'FixIt' : ( lambda self, request_data,
                         args: self._FixIt( request_data ) ) }


def ConvertCompletionData( completion ):
  return responses.BuildCompletionData(
    insertion_text = completion.insertion_text,
    menu_text = completion.menu_text,
    extra_menu_info = completion.extra_menu_info,
    kind = completion.kind,
    detailed_info = completion.detailed_info,
    extra_data = { 'doc_string': completion.extra_data } if completion.extra_data else None )


def DiagnosticsToDiagStructure( diagnostics ):
  structure = defaultdict( lambda : defaultdict( list ) )
  for diagnostic in diagnostics:
    structure[ diagnostic.location_.filename_ ][
      diagnostic.location_.line_number_ ].append( diagnostic )
  return structure
