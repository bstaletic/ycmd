// Copyright (C) 2011, 2012 Google Inc.
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

#include "IdentifierUtils.h"
#include "Utils.h"

#include <ctre/ctre.hpp>

#include <filesystem>
#include <unordered_map>

namespace YouCompleteMe {

namespace fs = std::filesystem;

namespace {

// For details on the tag format supported, see here for details:
// http://ctags.sourceforge.net/FORMAT
// TL;DR: The only supported format is the one Exuberant Ctags emits.
static constexpr ctll::fixed_string TAG_REGEX =
  "(?:^|\\r\\n|\\n)"          // Beginning of stream or a line separator
  "([^\\t\\n\\r]++)"          // The identifier
  "\\t"                       // A single tab is a field separator
  "([^\\t\\n\\r]++)"          // The path
  "\\t"                       // Field separator
  "[^\r\n]*?"                 // Junk until "language:" barring line separators
  "language:([^\\t\\n\\r]++)" // "language:" followed by language name
  "[^\r\n]*?"                 // Junk until the end of line or end of stream
			      // barring line separators
  "(?:$|\\r\\n|\\n)";         // Ending of stream or a line separator

// List of languages Universal Ctags supports:
//   ctags --list-languages
// To map a language name to a filetype, see this file:
//   :e $VIMRUNTIME/filetype.vim
const std::unordered_map < std::string_view,
                           std::string_view > LANG_TO_FILETYPE = {
        { "Ada"                 , "ada"                 },
        { "AnsiblePlaybook"     , "ansibleplaybook"     },
        { "Ant"                 , "ant"                 },
        { "Asm"                 , "asm"                 },
        { "Asp"                 , "asp"                 },
        { "Autoconf"            , "autoconf"            },
        { "Automake"            , "automake"            },
        { "Awk"                 , "awk"                 },
        { "Basic"               , "basic"               },
        { "BETA"                , "beta"                },
        { "C"                   , "c"                   },
        { "C#"                  , "cs"                  },
        { "C++"                 , "cpp"                 },
        { "Clojure"             , "clojure"             },
        { "Cobol"               , "cobol"               },
        { "CPreProcessor"       , "cpreprocessor"       },
        { "CSS"                 , "css"                 },
        { "ctags"               , "ctags"               },
        { "CUDA"                , "cuda"                },
        { "D"                   , "d"                   },
        { "DBusIntrospect"      , "dbusintrospect"      },
        { "Diff"                , "diff"                },
        { "DosBatch"            , "dosbatch"            },
        { "DTD"                 , "dtd"                 },
        { "DTS"                 , "dts"                 },
        { "Eiffel"              , "eiffel"              },
        { "elm"                 , "elm"                 },
        { "Erlang"              , "erlang"              },
        { "Falcon"              , "falcon"              },
        { "Flex"                , "flex"                },
        { "Fortran"             , "fortran"             },
        { "gdbinit"             , "gdb"                 },
        { "Glade"               , "glade"               },
        { "Go"                  , "go"                  },
        { "HTML"                , "html"                },
        { "Iniconf"             , "iniconf"             },
        { "ITcl"                , "itcl"                },
        { "Java"                , "java"                },
        { "JavaProperties"      , "jproperties"         },
        { "JavaScript"          , "javascript"          },
        { "JSON"                , "json"                },
        { "LdScript"            , "ldscript"            },
        { "Lisp"                , "lisp"                },
        { "Lua"                 , "lua"                 },
        { "M4"                  , "m4"                  },
        { "Make"                , "make"                },
        { "man"                 , "man"                 },
        { "MatLab"              , "matlab"              },
        { "Maven2"              , "maven2"              },
        { "Myrddin"             , "myrddin"             },
        { "ObjectiveC"          , "objc"                },
        { "OCaml"               , "ocaml"               },
        { "Pascal"              , "pascal"              },
        { "passwd"              , "passwd"              },
        { "Perl"                , "perl"                },
        { "Perl6"               , "perl6"               },
        { "PHP"                 , "php"                 },
        { "PlistXML"            , "plistxml"            },
        { "pod"                 , "pod"                 },
        { "Protobuf"            , "protobuf"            },
        { "PuppetManifest"      , "puppet"              },
        { "Python"              , "python"              },
        { "PythonLoggingConfig" , "pythonloggingconfig" },
        { "QemuHX"              , "qemuhx"              },
        { "R"                   , "r"                   },
        { "RelaxNG"             , "rng"                 },
        { "reStructuredText"    , "rst"                 },
        { "REXX"                , "rexx"                },
        { "Robot"               , "robot"               },
        { "RpmSpec"             , "spec"                },
        { "RSpec"               , "rspec"               },
        { "Ruby"                , "ruby"                },
        { "Rust"                , "rust"                },
        { "Scheme"              , "scheme"              },
        { "Sh"                  , "sh"                  },
        { "SLang"               , "slang"               },
        { "SML"                 , "sml"                 },
        { "SQL"                 , "sql"                 },
        { "SVG"                 , "svg"                 },
        { "SystemdUnit"         , "systemd"             },
        { "SystemVerilog"       , "systemverilog"       },
        { "Tcl"                 , "tcl"                 },
        { "TclOO"               , "tcloo"               },
        { "Tex"                 , "tex"                 },
        { "TTCN"                , "ttcn"                },
        { "Vera"                , "vera"                },
        { "Verilog"             , "verilog"             },
        { "VHDL"                , "vhdl"                },
        { "Vim"                 , "vim"                 },
        { "WindRes"             , "windres"             },
        { "XSLT"                , "xslt"                },
        { "YACC"                , "yacc"                },
        { "Yaml"                , "yaml"                },
        { "YumRepo"             , "yumrepo"             },
        { "Zephir"              , "zephir"              }
      };

}  // unnamed namespace


FiletypeIdentifierMap ExtractIdentifiersFromTagsFile(
  const fs::path &path_to_tag_file ) {
  FiletypeIdentifierMap filetype_identifier_map;
  std::string tags_file_contents;

  try {
    tags_file_contents = ReadUtf8File( path_to_tag_file );
  } catch ( ... ) {
    return filetype_identifier_map;
  }

  std::string::const_iterator start = tags_file_contents.begin();
  std::string::const_iterator end   = tags_file_contents.end();

  while ( auto matches = ctre::search< TAG_REGEX >( start, end ) ) {
    start = matches.get_end_position();

    auto language = matches.get< 3 >().to_view();

    std::string filetype{ FindWithDefault( LANG_TO_FILETYPE,
                                           language,
                                           Lowercase( language ) ) };
    auto identifier = matches.get< 1 >().to_view();
    fs::path path = fs::weakly_canonical( path_to_tag_file.parent_path() /
					  matches.get< 2 >().to_string() );

    filetype_identifier_map[ std::move( filetype ) ][ path.string() ]
      .emplace_back( identifier );
  }

  return filetype_identifier_map;
}

} // namespace YouCompleteMe
