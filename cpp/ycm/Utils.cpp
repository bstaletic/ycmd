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

#include "Utils.h"

#include <cmath>
#include <fstream>
#include <filesystem>
#include <limits>

namespace fs = std::filesystem;

namespace YouCompleteMe {

// Based on
// http://insanecoding.blogspot.fr/2011/11/how-to-read-in-file-in-c.html
std::string ReadUtf8File( const fs::path &filepath ) {
  std::string contents;
  // fs::is_empty() can throw basic_filesystem_error< Path > in case filepath
  // doesn't exist, or in case filepath's file_status is "other". "other" in
  // this case means everything that is not a regular file, directory or a
  // symlink.
  if ( !fs::is_empty( filepath ) && fs::is_regular_file( filepath ) ) {
    std::ifstream file( filepath, std::ios::in | std::ios::binary );
    file.seekg( 0, std::ios::end );
    contents.resize( file.tellg() );
    file.seekg( 0, std::ios::beg );
    file.read( &contents[ 0 ], contents.size() );
  }
  return contents;
}

} // namespace YouCompleteMe
