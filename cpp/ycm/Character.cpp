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

#include "Character.h"
#include "CodePoint.h"

#include <algorithm>
#include <numeric>

namespace YouCompleteMe {

namespace {

// Sort the code points according to the Canonical Ordering Algorithm.
// See https://www.unicode.org/versions/Unicode10.0.0/ch03.pdf#G49591
CodePointSequence CanonicalSort( CodePointSequence code_points ) {
  auto code_point_start = code_points.begin();

  while ( code_point_start != code_points.end() ) {
    if ( ( *code_point_start )->CombiningClass() == 0 ) {
      ++code_point_start;
      continue;
    }

    auto code_point_end = code_point_start + 1;
    while ( code_point_end != code_points.end() &&
            ( *code_point_end )->CombiningClass() != 0 ) {
      ++code_point_end;
    }

    std::sort( code_point_start,
               code_point_end,
               []( const CodePoint *left, const CodePoint *right ) {
                 return *left < *right;
               } );

    if ( code_point_end == code_points.end() ) {
      break;
    }

    code_point_start = code_point_end + 1;
  }

  return code_points;
}


// Decompose a UTF-8 encoded string into a sequence of code points according to
// Canonical Decomposition. See
// https://www.unicode.org/versions/Unicode10.0.0/ch03.pdf#G733
CodePointSequence CanonicalDecompose( const std::string &text ) {
  CodePointSequence code_points = BreakIntoCodePoints( text );
  std::string normal =
    std::accumulate( code_points.begin(),
                     code_points.end(),
                     std::string{},
                     [] ( std::string& current,
                          const CodePoint* cp ) {
                       return std::move( current ).append( cp->Normal() );
                     } );

  return CanonicalSort( BreakIntoCodePoints( normal ) );
}

} // unnamed namespace

Character::Character( const std::string &character )
  : is_base_( true ),
    is_letter_( false ),
    is_punctuation_( false ),
    is_uppercase_( false ) {
  // Normalize the character through NFD (Normalization Form D). See
  // https://www.unicode.org/versions/Unicode10.0.0/ch03.pdf#G49621
  CodePointSequence code_points = CanonicalDecompose( character );

  std::for_each( code_points.begin(),
                 code_points.end(),
                 [ & ] ( const CodePoint * cp ) {
                   normal_.append( cp->Normal() );
                   folded_case_.append( cp->FoldedCase() );
                   swapped_case_.append( cp->SwappedCase() );
                   is_letter_ |= cp->IsLetter();
                   is_punctuation_ |= cp->IsPunctuation();
                   is_uppercase_ |= cp->IsUppercase();
                   switch ( cp->GetBreakProperty() ) {
                     case BreakProperty::PREPEND:
                     case BreakProperty::EXTEND:
                     case BreakProperty::SPACINGMARK:
                       is_base_ = false;
                       break;
                     default:
                       base_.append( cp->FoldedCase() );
                   }
                 } );
}

} // namespace YouCompleteMe
