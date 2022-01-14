#! /Library/Frameworks/Python.framework/Versions/3.6/bin/python3.6


"""
Welcome to BaoPig

BAOPIG : Boite A Outils Pour Interfaces Graphiques

"""

# TODO : compliation executable
from baopig.version import *
print("Hello, this is baopig version", version)
import time
from pygame import *
from baopig.pybao.issomething import *
from baopig.pybao.objectutilities import Object, PrefilledFunction, PackedFunctions, \
                                         TypedDict, TypedList, TypedDeque, TypedSet

from baopig.ressources import *
from baopig.io import *
from baopig.time import *
from baopig._lib import *
from baopig.widgets import *

display = None  # protection for pygame.display

__version__ = str(version)


def debug_with_logging():

    LOGGER.add_debug_filehandler()
    LOGGER.cons_handler.setLevel(LOGGER.DEBUG)

