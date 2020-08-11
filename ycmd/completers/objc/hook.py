# Copyright (C) 2020 ycmd contributors
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

from ycmd.completers.cpp.clang_completer import ClangCompleter
from ycmd.completers.cpp.clangd_completer import ( ShouldEnableClangdCompleter,
                                                   ClangdCompleter )
from ycmd.utils import ImportCore
from typing import Dict, List, Union, Optional
ycm_core = ImportCore()


def GetCompleter( user_options: Dict[str, Union[int, Dict[str, int], List[str], str]] ) -> Optional[Union[ClangCompleter, ClangdCompleter]]:
  if ShouldEnableClangdCompleter( user_options ):
    return ClangdCompleter( user_options )
  if ycm_core.HasClangSupport():
    return ClangCompleter( user_options )
  return None
