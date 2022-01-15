

from baopig.pybao.objectutilities import Object
from baopig.pybao.issomething import *


class RessourcePack:

    def config(self, **kwargs):

        for name, value in kwargs.items():
            self.__setattr__('_'+name, value)


class FontsRessourcePack(RessourcePack):

    def __init__(self,
        file=None,
        height=15,
        color=(0, 0, 0),
    ):

        assert is_color(color)

        self._file = file
        self._height = height
        self._color = color

    file = property(lambda self: self._file)
    color = property(lambda self: self._color)
    height = property(lambda self: self._height)


class ScenesRessourcePack(RessourcePack):

    def __init__(self,
        background_color=(170, 170, 170),
    ):

        assert is_color(background_color)

        self._background_color = background_color

    background_color = property(lambda self: self._background_color)


# TODO : ButtonRessourcePack.style.create_surface(size)

class _RessourcePack:

    def __init__(self):

        self.font = FontsRessourcePack()
        self.scene = ScenesRessourcePack()

ressources = _RessourcePack()
