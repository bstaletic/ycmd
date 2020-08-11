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

from ycmd.completers.java.java_completer import (
  ShouldEnableJavaCompleter, JavaCompleter )
from typing import Dict, Optional, Union


def GetCompleter( user_options: Dict[str, Union[int, Dict[str, int], str]] ) -> Optional[JavaCompleter]:
  if not ShouldEnableJavaCompleter( user_options ):
    return None

  return JavaCompleter( user_options )
