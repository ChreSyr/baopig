

import pygame
from .utilities import paint_lock
from .widget import Widget, _Origin


class _Origin2(_Origin):
    """Optimized origin, only its position is configurable"""
    def __init__(self, owner):
        self._asked_pos = owner.pos
        self._from_hitbox = False
        self._owner_ref = owner.get_weakref()
        self._location = "topleft"
        self._reference_ref = self.owner.parent.get_weakref()
        self._reference_location = "topleft"

    pos = property(lambda self: self._asked_pos)

    def _reset_asked_pos(self):
        """
        This method should only be called by Widget._move()
        If the asked_pos was including percentage, and the percentage don't match anymore, it will be
        replaced by an integer value
        """
        self._asked_pos = self.owner.pos

    @staticmethod
    def accept(coord):
        if hasattr(coord, "__iter__"):
            if len(coord) != 2: return False
            return False not in (_Origin.accept(c) for c in coord)
        return isinstance(coord, (int, float))

    def config(self, pos=None, location=None, reference_comp=None, reference_location=None,
               from_hitbox=None, locked=None):
        raise PermissionError("Nope")


class AnimatedWidget(Widget):
    """
    Optimized class for widgets who move a lot
    """
    def __init__(self, *args, **kwargs):
        Widget.__init__(self, *args, **kwargs)
        assert not isinstance(self.origin.pos[0], str)
        assert not isinstance(self.origin.pos[1], str)
        assert self.origin.location == "topleft"
        assert self.origin.reference == self.parent
        assert self.origin.reference_location == "topleft"
        assert self.window is None
        self.move_at(kwargs["pos"])
        self._origin = _Origin2(self)

    # abs = abs_rect =    property(lambda self: self._abs_rect)
    # auto = auto_rect =  property(lambda self: self._auto_rect)
    # window =            property(lambda self: self._window)
    # hitbox =            property(lambda self: self._hitbox)
    # abs_hitbox =        property(lambda self: self._abs_hitbox)
    # auto_hitbox =       property(lambda self: self._auto_hitbox)

    def _move(self, dx, dy):

        old_hitbox = tuple(self.hitbox)
        with paint_lock:

            self.origin._asked_pos = (self.rect.left+dx, self.rect.top+dy)
            pygame.Rect.__setattr__(self.rect, "topleft", self.origin._asked_pos)
            self._hitbox = self.rect
            pygame.Rect.__setattr__(self.abs_rect, "topleft", (self.parent.abs.left + self.left, self.parent.abs.top + self.top))
            self._abs_hitbox = self.abs_rect

            self.signal.MOTION.emit(dx, dy)
            if self.is_visible:
                self.parent._warn_change(self.hitbox.union(old_hitbox))

    def set_window(self, window, follow_movements=None):

        raise PermissionError("A window is over-consuming...")

    def _set_surface(self, surface):

        with paint_lock:
            self._surface = surface
            size = surface.get_size()
            assert size != self.size
            if size != self.size:
                pygame.Rect.__setattr__(self.rect, "size", size)
                pygame.Rect.__setattr__(self.abs_rect, "size", size)
                pygame.Rect.__setattr__(self.auto_rect, "size", size)
                pygame.Rect.__setattr__(self.hitbox, "size", size)
                pygame.Rect.__setattr__(self.abs_hitbox, "size", size)
                pygame.Rect.__setattr__(self.auto_hitbox, "size", size)

