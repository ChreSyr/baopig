

import pygame

from baopig.pybao.issomething import *
from .layer import Layer
from .resizable import ResizableWidget
from .utilities import Color, paint_lock
from .widget import Widget


class Rectangle(ResizableWidget):
    """
    A Widget who is just a rectangle filled with one color

    If the border_width parameter is filled, the rectangle will not be filled, only its borders
    The border_width is given in pixels
    The border only goes inside the hitbox, not outside
    """

    STYLE = ResizableWidget.STYLE.substyle()
    STYLE.modify(
        width=30,
        height=30,
    )
    STYLE.create(
        color="theme-color-content",
        border_color="theme-color-border",
        border_width=0,
    )
    STYLE.set_type("color", Color)
    STYLE.set_type("border_color", Color)
    STYLE.set_type("border_width", int)
    STYLE.set_constraint("border_width", lambda val: val >= 0, "must be positive")

    def __init__(self, parent, **kwargs):

        ResizableWidget.__init__(self, parent, **kwargs)

        self._color = self.style["color"]
        self._border_color = self.style["border_color"]
        self._border_width = self.style["border_width"]

        self.paint()

    color = property(lambda self: self._color)
    border_color = property(lambda self: self._border_color)
    border_width = property(lambda self: self._border_width)

    def clip(self, rect):  # TODO : used ?
        """
        Clip the rectangle inside another (wich are both relative to the parent)
        """
        new_hitbox = self.hitbox.clip(rect)
        if new_hitbox == self.hitbox:
            return
        self.move_at(new_hitbox.topleft)
        self.resize(*new_hitbox.size)

    def handle_resize(self):
        self.send_paint_request()

    def paint(self):
        """
        If size is set, this method resizes the Rectangle
        """
        self.surface.fill(self.color)
        if self.border_color is not None:
            pygame.draw.rect(self.surface, self.border_color, (0, 0) + self.size, self.border_width * 2 - 1)

    def set_color(self, color=None):

        if color is None: color = (0, 0, 0, 0)
        self._color = Color(color)
        self.send_paint_request()

    def set_border_color(self, color):

        if not isinstance(color, Color):
            color = Color(color)

        assert is_color(color)
        self._border_color = color

        self.send_paint_request()

    def set_border_width(self, border_width):

        assert 0 <= border_width
        self._border_width = border_width

        self.send_paint_request()


class Highlighter_TBR(Widget):
    """
    A Highlighter is a border filled with one color surrounding a target's hitbox
    If the highlighter can be in the target's layer, it is placed in front of the target
    The border is one pixel inside the hitbox, so targets like scenes can be visually
    highlighted
    """

    def __init__(self, parent, target, color, width, **kwargs):

        # assert target.parent is parent
        if parent.parent == parent:
            parent = target  # target is a scene
        try:
            color = pygame.Color(color)
        except ValueError:
            color = pygame.Color(*color)

        size = (target.size[0] + width * 2 - 2, target.size[1] + width * 2 - 2)
        surface = pygame.Surface(size, pygame.SRCALPHA)
        pygame.draw.rect(surface, color, ((0, 0) + size), width * 2 - 1)

        Widget.__init__(
            self,
            parent=parent,
            surface=surface,
            pos=(-width + 1, -width + 1),
            pos_ref=target,
            **kwargs
        )

        self._color = color
        self._target_ref = target.get_weakref()
        self._width = width

        self.set_nontouchable()
        self.target.signal.RESIZE.connect(self.config, owner=self)

    color = property(lambda self: self._color)
    target = property(lambda self: self._target_ref())
    width = property(lambda self: self._width)

    def config(self, target=None, color=None, width=None):

        with paint_lock:

            if type(target) is tuple:  # old_size from RESIZE signal
                target = None

            if target is not None:
                try: self.target.signal.RESIZE.disconnect(self.config)
                except AttributeError: pass  # self.target = None
                self._target_ref = target.get_weakref()
                self.target.signal.RESIZE.connect(self.config, owner=self)
                w = self.width if width is None else width
                self.origin.config(pos=(-w+1, -w+1), reference_comp=self.target, from_hitbox=True)

            if color is not None:
                assert is_color(color)
                self._color = color

            if width is not None:
                assert 0 <= width
                self._width = width

            size = (self.target.hitbox.w + self.width * 2 - 2, self.target.hitbox.h + self.width * 2 - 2)
            if size != self.size:
                surface = pygame.Surface(size, pygame.SRCALPHA)
                pygame.draw.rect(surface, self.color, (0, 0) + size, self.width * 2 - 1)
                self.set_surface(surface)

    def set_border_width(self, border_width):

        raise NotImplemented


class Highlighter(Rectangle):
    """
    A Highlighter is a border filled with one color surrounding a target's hitbox
    If the highlighter can be in the target's layer, it is placed in front of the target
    The border is one pixel inside the hitbox, so targets like scenes can be visually
    highlighted
    """
    STYLE = Rectangle.STYLE.substyle()
    STYLE.modify(
        color=(0, 0, 0, 0),
        border_color="green",
        border_width=1,
    )

    def __init__(self, parent, target, **kwargs):

        if "pos_ref" in kwargs:
            raise PermissionError("Use 'target' instead of 'pos_ref'")
        if "size" in kwargs:
            raise PermissionError("A Highlighter's' size depends on its target")

        # assert target.parent is parent
        # if parent.parent == parent:  # TODO : move to debug_zone.py
        #     parent = target  # target is a scene

        Rectangle.__init__(self, parent, pos_ref=target, size=target.size, **kwargs)

        self._target_ref = target.get_weakref()
        self.set_nontouchable()
        self.target.signal.RESIZE.connect(self.handle_targetresize, owner=self)

    target = property(lambda self: self._target_ref())

    def config_TBR(self, target=None, color=None, width=None):

        with paint_lock:

            if type(target) is tuple:  # old_size from RESIZE signal
                target = None

            if target is not None:
                try:
                    self.target.signal.RESIZE.disconnect(self.config)
                except AttributeError:
                    pass  # self.target = None
                self._target_ref = target.get_weakref()
                self.target.signal.RESIZE.connect(self.config, owner=self)
                w = self.width if width is None else width
                self.origin.config(pos=(-w + 1, -w + 1), reference_comp=self.target, from_hitbox=True)

            if color is not None:
                assert is_color(color)
                self._color = color

            if width is not None:
                assert 0 <= width
                self._width = width

            size = (self.target.hitbox.w + self.width * 2 - 2, self.target.hitbox.h + self.width * 2 - 2)
            if size != self.size:
                surface = pygame.Surface(size, pygame.SRCALPHA)
                pygame.draw.rect(surface, self.color, (0, 0) + size, self.width * 2 - 1)
                self.set_surface(surface)

    def set_target(self, target, width):

        self.origin.config()

        try:
            self.target.signal.RESIZE.disconnect(self.config)
        except AttributeError:
            pass  # self.target = None
        self._target_ref = target.get_weakref()
        self.target.signal.RESIZE.connect(self.config, owner=self)
        w = self.width if width is None else width
        self.origin.config(pos=(-w + 1, -w + 1), reference_comp=self.target, from_hitbox=True)

    def handle_targetresize(self):

        self.resize(*self.target.size)


class Sail(Rectangle):
    STYLE = Rectangle.STYLE.substyle()
    STYLE.modify(
        border_width=0,
    )

    def __init__(self, *args, **kwargs):

        Rectangle.__init__(self, *args, **kwargs)
        self.set_nontouchable()
        if not self.parent.has_layer("nontouchable_layer"):
            Layer(self.parent, name="nontouchable_layer", touchable=False)
        self.swap_layer("nontouchable_layer")


class Polygon(Widget):
    """
    Create a Polygon from vertices
    If offset is set, move all vertices by offset
    """

    def __init__(self, parent, color, vertices, width=0, offset=(0, 0), offset_angle=None, **kwargs):

        assert "pos" not in kwargs, "Use offset instead"

        def plus(p1, p2):
            return p1[0] + p2[0], p1[1] + p2[1]
        def minus(p1, p2):
            return p1[0] - p2[0], p1[1] - p2[1]

        if offset_angle:
            import numpy
            rotation_matrix = numpy.array([[numpy.cos(offset_angle) ,-numpy.sin(offset_angle)],
                                           [numpy.sin(offset_angle) ,numpy.cos(offset_angle)]])
            vertices = tuple(rotation_matrix.dot(v) for v in vertices)

        topleft_corner = min(v[0] for v in vertices), min(v[1] for v in vertices)
        verts2 = tuple(minus(v, topleft_corner) for v in vertices)
        surf = pygame.Surface((
            max(v[0] for v in verts2)+1,
            max(v[1] for v in verts2)+1
        ), pygame.SRCALPHA)
        pygame.draw.polygon(surf, color, verts2, width)

        vertices = tuple(plus(offset, v) for v in vertices)
        pos = (
            min(v[0] for v in vertices),
            min(v[1] for v in vertices),
        )

        Widget.__init__(self, parent, surf, pos, **kwargs)

        self._vertices = vertices

    vertices = property(lambda self: self._vertices)


class Line(Widget):

    def __init__(self, parent, color, point_a, point_b, width=1, offset=(0, 0), offset_angle=None, **kwargs):

        assert "pos" not in kwargs, "Use offset instead"

        def plus(p1, p2):
            return p1[0] + p2[0], p1[1] + p2[1]
        def minus(p1, p2):
            return p1[0] - p2[0], p1[1] - p2[1]

        points = point_a, point_b
        if offset_angle:
            import numpy
            rotation_matrix = numpy.array([[numpy.cos(offset_angle) ,-numpy.sin(offset_angle)],
                                           [numpy.sin(offset_angle) ,numpy.cos(offset_angle)]])
            points = tuple(rotation_matrix.dot(p) for p in points)

        topleft_corner = min(p[0] for p in points), min(p[1] for p in points)
        points2 = tuple(minus(p, topleft_corner) for p in points)
        surf = pygame.Surface((
            max(p[0] for p in points2)+1,
            max(p[1] for p in points2)+1
        ), pygame.SRCALPHA)

        pygame.draw.line(surf, color, points2[0], points2[1], width)
        points = tuple(plus(offset, p) for p in points)
        pos = (
            min(p[0] for p in points),
            min(p[1] for p in points),
        )

        Widget.__init__(self, parent, surf, pos, **kwargs)

        self._points = points

    points = property(lambda self: self._points)


class Circle(Widget):

    def __init__(self, parent, color, center, radius, border_width=0, **kwargs):

        if isinstance(radius, float): radius = int(radius)
        assert "pos" not in kwargs, "Use center instead"
        assert isinstance(radius, int)
        if border_width > 1: raise NotImplemented
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, color, (radius, radius), radius, border_width)
        Widget.__init__(self, parent, surface=surf, pos=center, pos_location="center", **kwargs)

        self._color = color
        self._radius = radius
        self._border_width = border_width

    color = property(lambda self: self._color)
    radius = property(lambda self: self._radius)
    border_width = property(lambda self: self._border_width)

    def set_radius(self, radius):

        if isinstance(radius, float): radius = int(radius)
        assert isinstance(radius, int)
        assert radius >= 0

        self._radius = radius
        surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(surf, self.color, (radius, radius), radius, self.border_width)
        self.set_surface(surf)
