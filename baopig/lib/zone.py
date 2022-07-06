

import pygame
from baopig.lib import Container, paint_lock, Widget


class Zone(Container):

    STYLE = Container.STYLE.substyle()
    STYLE.modify(
        width=100,
        height=100,
    )

    def divide(self, side, width):
        # TODO : rework this function
        if side == "left":
            self.rect.left = width
            self.rect.w -= width
            if self.w <= 0:
                raise ValueError("the new zone shouldn't completly override the central zone")
            zone = Zone((width, self.rect.h))
        else:
            return
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

        self.parent.signal.NEW_SURF.connect(self._update_subsurface, owner=self)
        self.signal.MOTION.connect(self._update_subsurface, owner=self)

    def _update_subsurface(self):

        with paint_lock:
            try:
                Widget.set_surface(self, self.parent.surface.subsurface(self.pos + self.size))
            except ValueError:
                assert not self.parent.auto.contains(self.rect)
                Widget.set_surface(self, self.parent.surface.subsurface(
                    pygame.Rect(self.rect).clip(self.parent.auto)))  # resize the subzone

    def _flip(self):  # TODO : check with new padding & etc
        """Update all the surface"""

        if self.is_hidden:
            return

        with paint_lock:

            self._flip_without_update()

            # optimization
            if self.parent is self.scene:
                pygame.display.update(self.hitbox)
            else:
                self.parent.send_display_request(
                    rect=(self.parent.left + self.hitbox.left, self.parent.top + self.hitbox.top) + self.hitbox.size
                )

    def _warn_parent(self, rect):
        """Request updates at rects referenced by self"""

        rect = (self.left + rect[0], self.top + rect[1]) + tuple(rect[2:])

        # because of subsurface, we can skip self.parent._update_rect()
        if self.parent is self.scene:
            pygame.display.update(rect)
        else:
            self.parent._warn_parent(rect)

    def resize(self, w, h):

        if self.has_locked.width:
            raise PermissionError("Cannot resize : the width is locked")
        if self.has_locked.height:
            raise PermissionError("Cannot resize : the height is locked")
        # if (w, h) == self._asked_size:
        #     return

        self._asked_size = w, h

        asked_size = self._get_asked_size()
        if asked_size == self.size:
            return

        # self.set_surface(pygame.Surface(asked_size, pygame.SRCALPHA))

        with paint_lock:
            try:
                Widget.set_surface(self, self.parent.surface.subsurface(self.pos + asked_size))
            except ValueError:
                assert not self.parent.auto.contains(self.rect)
                raise PermissionError("A SubZone must fit inside its parent")
            self._flip_without_update()
