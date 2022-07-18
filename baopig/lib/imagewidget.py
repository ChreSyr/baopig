
# NOTE : filename is imagewidget.py because image.py would overlap pygame.image

import pygame
from .widget import Widget


class Image(Widget):

    # TODO : self.tiled instead of parameter in resize()

    def __init__(self, parent, image, w=None, h=None, tiled=False, **kwargs):  # TODO : rework w & h params
        """
        Cree une image

        If w or h parameters are filled, width or height of image argument
        are respectively resized
        """

        assert isinstance(image, pygame.Surface), "image must be a Surface"

        image_size = image.get_size()
        if w is None:
            w = image_size[0]
        if h is None:
            h = image_size[1]
        if image_size != (w, h):
            surface = pygame.transform.scale(image, (w, h))
        else:
            surface = image.copy()

        Widget.__init__(self, parent=parent, surface=surface, **kwargs)
        if self._asked_size[0] is None:
            self._asked_size = (self.rect.w, self._asked_size[1])
        if self._asked_size[1] is None:
            self._asked_size = (self._asked_size[0], self.rect.h)

        self._original = image
        self._tiled = tiled

    def _update_surface_from_resize(self, asked_size):

        if self._tiled:
            super()._update_surface_from_resize(asked_size)

        else:
            self.set_surface(pygame.transform.scale(self._original, asked_size))

    def collidemouse_alpha(self):  # TODO
        raise NotImplemented

    def paint(self):  # TODO : tests

        if self._tiled:

            width, height = self.rect.size
            self.surface.blit(self._original, (0, 0))
            original_w, original_h = self._original.get_size()

            if width > original_w:
                for i in range(int(width / original_w)):
                    self.surface.blit(self.surface, (original_w * (i + 1), 0))

            if height > original_h:
                row = self.surface.subsurface((0, 0, width, original_h)).copy()
                for i in range(int(height / original_h)):
                    self.surface.blit(row, (0, original_h * (i + 1)))
