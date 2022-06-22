
"""
Welcome to BaoPig

BAOPIG : Boite A Outils Pour Interfaces Graphiques

"""

print("baopig from WIP")

# TODO : compilation executable
from .version.version import version
print(f"baopig {version} - ", end="")
from pygame import *
from .pybao.issomething import *
from .pybao.objectutilities import Object, PrefilledFunction, PackedFunctions

from .io import *
from .time import *
from ._lib import *
from .widgets import *

display = None  # protection for pygame.display

__version__ = str(version)


def debug_with_logging():

    LOGGER.add_debug_filehandler()
    LOGGER.cons_handler.setLevel(LOGGER.DEBUG)

