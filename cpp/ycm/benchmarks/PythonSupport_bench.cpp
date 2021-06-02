// Copyright (C) 2017-2018 ycmd contributors
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

#include "BenchUtils.h"
#include "PythonSupport.h"
#include "Repository.h"

#include <benchmark/benchmark.h>

namespace YouCompleteMe {

class PythonSupportFixture : public benchmark::Fixture {
public:
  void SetUp( const benchmark::State& ) {
    Repository< CodePoint >::Instance().ClearElements();
    Repository< Character >::Instance().ClearElements();
    Repository< Candidate >::Instance().ClearElements();
  }
};


BENCHMARK_DEFINE_F( PythonSupportFixture,
                    FilterAndSortUnstoredCandidatesWithCommonPrefix )(
    benchmark::State& state ) {

  std::vector< std::string > raw_candidates;
  raw_candidates = GenerateCandidatesWithCommonPrefix( "a_A_a_",
                                                       state.range( 0 ) );

  for ( auto _ : state ) {
    state.PauseTiming();
    Repository< Character >::Instance().ClearElements();
    Repository< Candidate >::Instance().ClearElements();
    auto candidates_copy = raw_candidates;
    std::string query = "aA";
    state.ResumeTiming();
    CppFilterAndSortCandidates( std::move( candidates_copy ), std::move( query ),
                             state.range( 1 ) );
  }

  state.SetComplexityN( state.range( 0 ) );
}


BENCHMARK_DEFINE_F( PythonSupportFixture,
                    FilterAndSortStoredCandidatesWithCommonPrefix )(
    benchmark::State& state ) {

  std::vector< std::string > raw_candidates;
  raw_candidates = GenerateCandidatesWithCommonPrefix( "a_A_a_",
                                                       state.range( 0 ) );

  pybind11::str candidate_property("insertion_text");
  // Store the candidates in the repository.
  std::string query = "aA";
  CppFilterAndSortCandidates( std::vector(raw_candidates), std::move( query ),
                           state.range( 1 ) );

  for ( auto _ : state ) {
    state.PauseTiming();
    auto candidates_copy = raw_candidates;
    std::string query = "aA";
    state.ResumeTiming();
    CppFilterAndSortCandidates( std::move( candidates_copy ), std::move( query ),
                             state.range( 1 ) );
  }

  state.SetComplexityN( state.range( 0 ) );
}


BENCHMARK_REGISTER_F( PythonSupportFixture,
                      FilterAndSortUnstoredCandidatesWithCommonPrefix )
    ->RangeMultiplier( 1 << 4 )
    ->Ranges( { { 1, 1 << 16 }, { 0, 0 } } )
    ->Complexity();

BENCHMARK_REGISTER_F( PythonSupportFixture,
                      FilterAndSortUnstoredCandidatesWithCommonPrefix )
    ->RangeMultiplier( 1 << 4 )
    ->Ranges( { { 1, 1 << 16 }, { 50, 50 } } )
    ->Complexity();


BENCHMARK_REGISTER_F( PythonSupportFixture,
                      FilterAndSortStoredCandidatesWithCommonPrefix )
    ->RangeMultiplier( 1 << 4 )
    ->Ranges( { { 1, 1 << 16 }, { 0, 0 } } )
    ->Complexity();

BENCHMARK_REGISTER_F( PythonSupportFixture,
                      FilterAndSortStoredCandidatesWithCommonPrefix )
    ->RangeMultiplier( 1 << 4 )
    ->Ranges( { { 1, 1 << 16 }, { 50, 50 } } )
    ->Complexity();

} // namespace YouCompleteMe
