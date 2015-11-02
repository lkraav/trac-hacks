# Creado por Olemis Lang el 7/3/2009 12:31AM.
# Copyright (c) 2009 Olemis Lang. All rights reserved.

from trac.core import *

from themeengine.api import ThemeBase

class ExampleTheme(ThemeBase):
    """Un tema sencillo para Trac."""
    
    htdocs = css = screenshot = True
    
