

import pygame
from baopig._debug import debug_screen_updates, debug_with_assert
from baopig.io.logging import LOGGER
from baopig._lib import Box, Layer, paint_lock, Widget, Size


class Zone(Box):  # TODO : BoxModel

    STYLE = Box.STYLE.substyle()
    STYLE.modify(
        width = 100,
        height = 100,
    )

    def __init__(self, parent, **options):

        Box.__init__(self, parent, **options)

    def divide(self, side, width):
        # TODO : rework this function
        if side == "left":
            self.rect.left = width
            self.rect.w -= width
            if self.w <= 0:
                raise ValueError("the new zone shouldn't completly override the central zone")
            zone = Zone((width, self.rect.h))
            comps_to_move = []  # On ne peut iterer sur une liste tout en la modifiant
            for comp in self._components:
                if zone.hitbox.collidepoint(comp.topleft):
                    comps_to_move.append(comp)
                else:
                    comp.left -= width
            for comp in comps_to_move:
                zone.append(comp)
                self.remove(comp)
        return zone


class SubZone(Zone):  # TODO : SubScene ? with rects_to_update ?
    # TODO : solve : when update on a SubZone whose parent is a scene, the display isn't updated
    """A SuzZone is an optimized Zone, its surface is a subsurface of its parent (cannot have transparency)"""

    def __init__(self, parent, **kwargs):

        Zone.__init__(self, parent, **kwargs)
        try:
            self._surface = self.parent.surface.subsurface(self.pos + self.size)
        except ValueError:
            assert not self.parent.auto.contains(self.rect)
            raise PermissionError("A SubZone must fit inside its parent")
        if debug_with_assert: assert self.surface.get_parent() is self.parent.surface

        self.connect("_update_subsurface", self.parent.signal.NEW_SURF)
        self.connect("_update_subsurface", self.signal.MOTION)

    def _update_subsurface(self):

        with paint_lock:
            try:
                Widget.set_surface(self, self.parent.surface.subsurface(self.pos + self.size))
            except ValueError:
                assert not self.parent.auto.contains(self.rect)
                Widget.set_surface(self, self.parent.surface.subsurface(
                    pygame.Rect(self.rect).clip(self.parent.auto)))  # resize the subzone
            if debug_with_assert: assert self.surface.get_parent() is self.parent.surface

    def _flip(self):
        """Update all the surface"""

        if self.is_hidden:  return

        with paint_lock:

            self._flip_without_update()

            # optimization
            if self.parent is self.scene:
                pygame.display.update(self.hitbox)
            else:
                self.parent.parent._warn_change(
                    (self.parent.left + self.hitbox.left, self.parent.top + self.hitbox.top) + tuple(self.hitbox.size)
                )
            if debug_with_assert: assert self.surface.get_parent() is self.parent.surface

    def _warn_parent(self, rect):
        """Request updates at rects referenced by self"""

        rect = (self.left + rect[0], self.top + rect[1]) + tuple(rect[2:])

        # because of subsurface, we can skip self.parent._update_rect()
        if self.parent is self.scene:
            pygame.display.update(rect)
        else:
            self.parent._warn_parent(rect)
        if debug_with_assert: assert self.surface.get_parent() is self.parent.surface

    def resize(self, w, h):

        if self.has_locked.width: w = self.w
        if self.has_locked.height: h = self.h
        if (w, h) == self.size: return

        with paint_lock:
            try:
                Widget.set_surface(self, self.parent.surface.subsurface(self.pos + (w, h)))
            except ValueError:
                assert not self.parent.auto.contains(self.rect)
                raise PermissionError("A SubZone must fit inside its parent")
                Widget.set_surface(self, self.parent.surface.subsurface(
                    pygame.Rect(self.pos + (w, h)).clip(self.parent.auto)))
            self._flip_without_update()

        # print("RESIZED", self, "at", size)
