
import threading
import pygame

paint_lock = threading.RLock()

# TODO : deproteger les attributs handle_something


class Size(tuple):

    def __init__(self, size):
        assert len(self) == 2, f"Wrong length : {self} (a size only have 2 elements)"
        for coord in self:
            assert isinstance(coord, (int, float)), f"Wrong value in size : {coord} (must be a number)"
            assert coord >= 0, f"Wrong value in size : {coord} (must be positive)"


class Color(pygame.Color):
    """
    Very close to pygame.Color :

    Color(tuple) -> Color
    Color(name) -> Color
    Color(r, g, b, a) -> Color
    Color(rgbvalue) -> Color
    pygame object for color representations
    """

    def __init__(self, *args, transparency=None, **kwargs):

        if transparency is None:
            try:
                pygame.Color.__init__(self, *args, **kwargs)
            except ValueError:
                pygame.Color.__init__(self, *args[0])

        else:
            try:
                color = pygame.Color(*args, **kwargs)
            except ValueError:
                color = pygame.Color(*args[0])
            pygame.Color.__init__(self, color.r, color.g, color.b, transparency)

    def set_hsv(self, val):
        if val[1] > 100:
            val = val[0], 100, val[2]
        try:
            self.hsva = val + (100,)
        except ValueError as e:
            raise ValueError(str(e) + f" : {val}")
    hsv = property(lambda self: self.hsva[:-1], set_hsv)

    def set_hsl(self, val):
        if val[1] > 100:
            val = val[0], 100, val[2]
        try:
            self.hsla = val + (100,)
        except ValueError as e:
            raise ValueError(str(e) + f" : {val}")
    hsl = property(lambda self: self.hsla[:-1], set_hsl)

    def set_hue(self, h):
        self.hsv = (h,) + self.hsv[1:]
    h = property(lambda self: self.hsva[0], set_hue)

    def get_saturation(self):
        s = self.hsva[1]
        if s > 100:  # sometime 100.00000000000001
            s = 100
        return s
    def set_saturation(self, s):
        self.hsv = self.h, s, self.v
    s = property(get_saturation, set_saturation)

    def set_value(self, v):
        self.hsv = self.hsva[:2] + (v,)
    v = property(lambda self: self.hsva[2], set_value)

    def set_lightness(self, l):
        self.hsl = self.hsla[:2] + (l,)
    l = property(lambda self: self.hsla[2], set_lightness)

    def copy(self):
        return self.__class__(self)

    def has_transparency(self):

        return self.a < 255


class MarginType:
    # Once it is created, it can never change

    def __init__(self, margin):

        if margin is None:
            margin = 0, 0, 0, 0
        elif isinstance(margin, int):
            margin = tuple([margin] * 4)
        elif isinstance(margin, MarginType):
            margin = margin.left, margin.top, margin.right, margin.bottom
        else:
            l = len(margin)
            if l == 2:
                margin = tuple(margin) + tuple(margin)
            elif l == 3:
                margin = tuple(margin) + tuple([margin[1]])
            else:
                assert l == 4, f"Wrong value for margin type : {margin}"

        self._left = margin[0]
        self._top = margin[1]
        self._right = margin[2]
        self._bottom = margin[3]

    def __repr__(self):
        return f"MarginType(left={self.left}, top={self.top}, right={self.right}, bottom={self.bottom})"

    bottom = property(lambda self: self._bottom)
    is_null = property(lambda self: self.left == self.top == self.right == self.bottom == 0)
    left = property(lambda self: self._left)
    right = property(lambda self: self._right)
    top = property(lambda self: self._top)


class Handler_SceneOpen:
    """
    A Handler_SceneOpen is a widget whose 'handle_scene_open' function is called when its scene gets open
    """
    def handle_scene_open(self):
        """Stuff to do when the widget's scene gets open"""


class Handler_SceneClose:
    """
    A Handler_SceneClose is a widget whose 'handle_scene_close' function is called when its scene is closed
    """
    def handle_scene_close(self):
        """Stuff to do when the widget'scene is closed"""
