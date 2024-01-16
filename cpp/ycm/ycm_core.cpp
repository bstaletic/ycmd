// Copyright (C) 2011-2018 ycmd contributors
//
// This file is part of ycmd.
//
// ycmd is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// ycmd is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with ycmd.  If not, see <http://www.gnu.org/licenses/>.

#include "Candidate.h"
#include "CodePoint.h"
#include "IdentifierCompleter.h"
#include "PythonSupport.h"
#include "versioning.h"

#ifdef USE_CLANG_COMPLETER
#  include "ClangCompleter.h"
#  include "ClangUtils.h"
#  include "CompilationDatabase.h"
#  include "CompletionData.h"
#  include "Diagnostic.h"
#  include "Documentation.h"
#  include "Location.h"
#  include "Range.h"
#  include "UnsavedFile.h"
#endif // USE_CLANG_COMPLETER

#include <nanobind/stl/bind_vector.h>
#include <nanobind/stl/string.h>

namespace py = nanobind;
using namespace YouCompleteMe;

static bool HasClangSupport() {
#ifdef USE_CLANG_COMPLETER
  return true;
#else
  return false;
#endif // USE_CLANG_COMPLETER
}

NB_MAKE_OPAQUE( std::vector< std::string > )
#ifdef USE_CLANG_COMPLETER
NB_MAKE_OPAQUE( std::vector< UnsavedFile > )
NB_MAKE_OPAQUE( std::vector< Range > )
NB_MAKE_OPAQUE( std::vector< CompletionData > )
NB_MAKE_OPAQUE( std::vector< Diagnostic > )
NB_MAKE_OPAQUE( std::vector< FixIt > )
NB_MAKE_OPAQUE( std::vector< FixItChunk > )
#endif // USE_CLANG_COMPLETER

NB_MODULE( ycm_core, mod )
{
  mod.def( "HasClangSupport", &HasClangSupport );

  mod.def( "FilterAndSortCandidates",
           &FilterAndSortCandidates,
           py::arg("candidates"),
           py::arg("candidate_property"),
           py::arg("query"),
           py::arg("max_candidates") = 0 );

  mod.def( "YcmCoreVersion", &YcmCoreVersion );

  // This is exposed so that we can test it.
  mod.def( "GetUtf8String", []( py::handle o ) -> py::bytes {
    std::string output = GetUtf8String( o );
    return py::steal<py::bytes>(PyBytes_FromStringAndSize(output.data(), output.size())); } );

  py::class_< IdentifierCompleter >( mod, "IdentifierCompleter" )
    .def( py::init<>() )
    .def( "AddSingleIdentifierToDatabase",
          &IdentifierCompleter::AddSingleIdentifierToDatabase,
          py::call_guard< py::gil_scoped_release >() )
    .def( "ClearForFileAndAddIdentifiersToDatabase",
          &IdentifierCompleter::ClearForFileAndAddIdentifiersToDatabase,
          py::call_guard< py::gil_scoped_release >() )
    .def( "AddIdentifiersToDatabaseFromTagFiles",
          &IdentifierCompleter::AddIdentifiersToDatabaseFromTagFiles,
          py::call_guard< py::gil_scoped_release >() )
    .def( "CandidatesForQueryAndType",
          &IdentifierCompleter::CandidatesForQueryAndType,
          py::call_guard< py::gil_scoped_release >(),
          py::arg( "query" ),
          py::arg( "filetype" ),
          py::arg( "max_candidates" ) = 0 );

  py::bind_vector< std::vector< std::string > >( mod, "StringVector" );

#ifdef USE_CLANG_COMPLETER
  py::exception< ClangParseError >( mod, "ClangParseError" );

  mod.def( "ClangVersion", ClangVersion );

  // CAREFUL HERE! For filename and contents we are referring directly to
  // Python-allocated and -managed memory since we are accepting pointers to
  // data members of python objects. We need to ensure that those objects
  // outlive our UnsavedFile objects.
  py::class_< UnsavedFile >( mod, "UnsavedFile" )
    .def( py::init<>() )
    .def_rw( "filename_", &UnsavedFile::filename_ )
    .def_rw( "contents_", &UnsavedFile::contents_ )
    .def_rw( "length_", &UnsavedFile::length_ );

  py::bind_vector< std::vector< UnsavedFile > >( mod, "UnsavedFileVector" );

  py::class_< ClangCompleter >( mod, "ClangCompleter" )
    .def( py::init<>() )
    .def( "GetDeclarationLocation",
          &ClangCompleter::GetDeclarationLocation,
          py::call_guard< py::gil_scoped_release >() )
    .def( "GetDefinitionLocation",
          &ClangCompleter::GetDefinitionLocation,
          py::call_guard< py::gil_scoped_release >() )
    .def( "GetDefinitionOrDeclarationLocation",
          &ClangCompleter::GetDefinitionOrDeclarationLocation,
          py::call_guard< py::gil_scoped_release >() )
    .def( "DeleteCachesForFile",
          &ClangCompleter::DeleteCachesForFile,
          py::call_guard< py::gil_scoped_release >() )
    .def( "UpdatingTranslationUnit",
          &ClangCompleter::UpdatingTranslationUnit,
          py::call_guard< py::gil_scoped_release >() )
    .def( "UpdateTranslationUnit",
          &ClangCompleter::UpdateTranslationUnit,
          py::call_guard< py::gil_scoped_release >() )
    .def( "CandidatesForLocationInFile",
          &ClangCompleter::CandidatesForLocationInFile,
          py::call_guard< py::gil_scoped_release >() )
    .def( "GetTypeAtLocation",
          &ClangCompleter::GetTypeAtLocation,
          py::call_guard< py::gil_scoped_release >() )
    .def( "GetEnclosingFunctionAtLocation",
          &ClangCompleter::GetEnclosingFunctionAtLocation,
          py::call_guard< py::gil_scoped_release >() )
    .def( "GetFixItsForLocationInFile",
          &ClangCompleter::GetFixItsForLocationInFile,
          py::call_guard< py::gil_scoped_release >() )
    .def( "GetDocsForLocationInFile",
          &ClangCompleter::GetDocsForLocationInFile,
          py::call_guard< py::gil_scoped_release >() );

  py::enum_< CompletionKind >( mod, "CompletionKind" )
    .value( "STRUCT", CompletionKind::STRUCT )
    .value( "CLASS", CompletionKind::CLASS )
    .value( "ENUM", CompletionKind::ENUM )
    .value( "TYPE", CompletionKind::TYPE )
    .value( "MEMBER", CompletionKind::MEMBER )
    .value( "FUNCTION", CompletionKind::FUNCTION )
    .value( "VARIABLE", CompletionKind::VARIABLE )
    .value( "MACRO", CompletionKind::MACRO )
    .value( "PARAMETER", CompletionKind::PARAMETER )
    .value( "NAMESPACE", CompletionKind::NAMESPACE )
    .value( "UNKNOWN", CompletionKind::UNKNOWN );

  py::class_< CompletionData >( mod, "CompletionData" )
    .def( py::init<>() )
    .def( "TextToInsertInBuffer", &CompletionData::TextToInsertInBuffer )
    .def( "MainCompletionText", &CompletionData::MainCompletionText )
    .def( "ExtraMenuInfo", &CompletionData::ExtraMenuInfo )
    .def( "DetailedInfoForPreviewWindow",
          &CompletionData::DetailedInfoForPreviewWindow )
    .def( "DocString", &CompletionData::DocString )
    .def_ro( "kind_", &CompletionData::kind_ )
    .def_ro( "fixit_", &CompletionData::fixit_ );

  py::bind_vector< std::vector< CompletionData > >( mod,
                                                    "CompletionVector" );

  py::class_< Location >( mod, "Location" )
    .def( py::init<>() )
    .def_ro( "line_number_", &Location::line_number_ )
    .def_ro( "column_number_", &Location::column_number_ )
    .def_ro( "filename_", &Location::filename_ )
    .def( "IsValid", &Location::IsValid );

  py::class_< Range >( mod, "Range" )
    .def( py::init<>() )
    .def_ro( "start_", &Range::start_ )
    .def_ro( "end_", &Range::end_ );

  py::bind_vector< std::vector< Range > >( mod, "RangeVector" );

  py::class_< FixItChunk >( mod, "FixItChunk" )
    .def( py::init<>() )
    .def_ro( "replacement_text", &FixItChunk::replacement_text )
    .def_ro( "range", &FixItChunk::range );

  py::bind_vector< std::vector< FixItChunk > >( mod, "FixItChunkVector" );

  py::class_< FixIt >( mod, "FixIt" )
    .def( py::init<>() )
    .def_ro( "chunks", &FixIt::chunks )
    .def_ro( "location", &FixIt::location )
    .def_ro( "text", &FixIt::text )
    .def_prop_ro( "kind", [](const py::handle) {
      return py::none();
    });

  py::bind_vector< std::vector< FixIt > >( mod, "FixItVector" );

  py::enum_< DiagnosticKind >( mod, "DiagnosticKind" )
    .value( "ERROR", DiagnosticKind::ERROR )
    .value( "WARNING", DiagnosticKind::WARNING )
    .value( "INFORMATION", DiagnosticKind::INFORMATION );

  py::class_< Diagnostic >( mod, "Diagnostic" )
    .def( py::init<>() )
    .def_ro( "ranges_", &Diagnostic::ranges_ )
    .def_ro( "location_", &Diagnostic::location_ )
    .def_ro( "location_extent_", &Diagnostic::location_extent_ )
    .def_ro( "kind_", &Diagnostic::kind_ )
    .def_ro( "text_", &Diagnostic::text_ )
    .def_ro( "long_formatted_text_", &Diagnostic::long_formatted_text_ )
    .def_ro( "fixits_", &Diagnostic::fixits_ );

  py::bind_vector< std::vector< Diagnostic > >( mod, "DiagnosticVector" );

  py::class_< DocumentationData >( mod, "DocumentationData" )
    .def( py::init<>() )
    .def_ro( "comment_xml", &DocumentationData::comment_xml )
    .def_ro( "raw_comment", &DocumentationData::raw_comment )
    .def_ro( "brief_comment", &DocumentationData::brief_comment )
    .def_ro( "canonical_type", &DocumentationData::canonical_type )
    .def_ro( "display_name", &DocumentationData::display_name );

  py::class_< CompilationDatabase >( mod, "CompilationDatabase" )
    .def( py::init< py::object >() )
    .def( "DatabaseSuccessfullyLoaded",
          &CompilationDatabase::DatabaseSuccessfullyLoaded )
    .def( "AlreadyGettingFlags",
          &CompilationDatabase::AlreadyGettingFlags )
    .def( "GetCompilationInfoForFile",
          &CompilationDatabase::GetCompilationInfoForFile )
    .def_prop_ro( "database_directory",
                  &CompilationDatabase::GetDatabaseDirectory );

  py::class_< CompilationInfoForFile >( mod, "CompilationInfoForFile" )
    .def_ro( "compiler_working_dir_",
             &CompilationInfoForFile::compiler_working_dir_ )
    .def_ro( "compiler_flags_",
             &CompilationInfoForFile::compiler_flags_ );

#endif // USE_CLANG_COMPLETER
}
