#!/usr/bin/env python

import swift_ycm_core
from ycmd.completers.swift.swift_completer import SwiftCompleter

def GetCompleter( user_options ):
  if swift_ycm_core.is_initialized():
    return SwiftCompleter( user_options )
  else:
    return None
