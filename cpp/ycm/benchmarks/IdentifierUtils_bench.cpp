// Copyright (C) 2018 ycmd contributors
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

#include <benchmark/benchmark_api.h>
#include <fstream>
#include <iostream>

namespace YouCompleteMe {

class IdentifierUtilsFixture : public benchmark::Fixture {
public:
  void SetUp( const benchmark::State &state ) {
    std::string tag_file_contents;

    for ( int i = 0; i < state.range( 0 ); ++i ) {
      std::string candidate = "";
      int letter = i;
      for ( int pos = 0; pos < 5; letter /= 26, ++pos ) {
        candidate = std::string( 1, letter % 26 + 'a' ) + candidate;
      }
      tag_file_contents += candidate + "\t/foo\tlanguage:C++\n";
    }

    std::ofstream tag_file( tag_path.string() );
    tag_file << tag_file_contents;
    tag_file.close();
    std_tag_path = tag_path.string();
  }

  void TearDown( const benchmark::State& ) {
    fs::remove( tag_path );
  }

  fs::path tag_path = "temp_file";
  fs::path std_tag_path;
};


BENCHMARK_DEFINE_F( IdentifierUtilsFixture,
                    ExtractIdentifiersFromTagsFileBench )(
  benchmark::State& state ) {

  while ( state.KeepRunning() ) {
    ExtractIdentifiersFromTagsFile( std_tag_path );
  }

  state.SetComplexityN( state.range( 0 ) );
}

BENCHMARK_REGISTER_F( IdentifierUtilsFixture,
                      ExtractIdentifiersFromTagsFileBench )
  ->RangeMultiplier( 1 << 4 )
  ->Range( 1, 1 << 16 )
  ->Complexity();

} // namespace YouCompleteMe
