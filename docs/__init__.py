#! /Library/Frameworks/Python.framework/Versions/3.6/bin/python3.6


"""
Welcome to BaoPig

BAOPIG : Boite A Outils Pour Interfaces Graphiques

"""

# TODO : compliation executable
from docs.version import *
print("Hello, this is baopig version", version)
from pygame import *
from .pybao.issomething import *
from .pybao.objectutilities import Object, PrefilledFunction, PackedFunctions, \
                                         TypedDict, TypedList, TypedDeque, TypedSet

from .ressources import *
from .io import *
from .time import *
from ._lib import *
from .widgets import *

display = None  # protection for pygame.display

__version__ = str(version)


def debug_with_logging():

    LOGGER.add_debug_filehandler()
    LOGGER.cons_handler.setLevel(LOGGER.DEBUG)

