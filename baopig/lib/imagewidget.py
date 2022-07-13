
# NOTE : filename is imagewidget.py because image.py would overlap pygame.image

import pygame
from .widget_supers import ResizableWidget


class Image(ResizableWidget):

    # TODO : self.tiled instead of parameter in resize()

    def __init__(self, parent, image, w=None, h=None, **kwargs):  # TODO : rework w & h params
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

        ResizableWidget.__init__(self, parent=parent, surface=surface, **kwargs)
        if self._asked_size[0] is None:
            self._asked_size = (self.rect.w, self._asked_size[1])
        if self._asked_size[1] is None:
            self._asked_size = (self._asked_size[0], self.rect.h)

        self._original = image

    def collidemouse_alpha(self):  # TODO
        raise NotImplemented

    def resize(self, w, h, tiled=False):

        super().resize(w, h)

        if tiled:

            surface = self.surface
            surface.blit(self._original, (0, 0))
            original_w, original_h = self._original.get_size()

            if self.rect.w > original_w:
                for i in range(int(self.rect.w / original_w)):
                    surface.blit(self.surface, (original_w * (i + 1), 0))

            if self.rect.h > original_h:
                row = surface.subsurface((0, 0, self.rect.w, original_h)).copy()
                for i in range(int(self.rect.h / original_h)):
                    surface.blit(row, (0, original_h * (i + 1)))

            self.set_surface(surface)

        else:
            self.set_surface(pygame.transform.scale(self._original, self.rect.size))
