"""
This package contains a simple preprocessor inspired by the C preprocessor.
For more information, see: https://github.com/Lesbre/preprocessor/
It contains:
- the Preprocessor class - use to configure an run the preprocessor
- constants PREPROCESSOR_NAME and PREPROCESSOR_VERSION
- the WarningMode enum used to configure the Preprocessor class
- the FileDescriptor class used to initialize contexts
  (used to traceback errors to input files)
"""

from .context import FileDescriptor
from .defaults import Preprocessor
from .defs import PREPROCESSOR_NAME, PREPROCESSOR_VERSION, WarningMode
