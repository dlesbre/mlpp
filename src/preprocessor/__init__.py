"""
This is the __init__.py file
It imports:
- the Preprocessor class from .preprocessor
  and adds all the default commands and blocks from .default
- constants PREPROCESSOR_NAME and PREPROCESSOR_VERSION from .defs
- the WarningMode enum used to configure the Preprocessor from .defs
- the FileDescriptor class used to initialize contexts from .context
"""

from .context import FileDescriptor
from .defaults import Preprocessor
from .defs import PREPROCESSOR_NAME, PREPROCESSOR_VERSION, WarningMode
