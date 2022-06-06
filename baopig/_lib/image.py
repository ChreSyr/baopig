

import pygame
from pygame.image import *  # so baopig.image contains pygame.image
from .resizable import ResizableWidget


class Image(ResizableWidget):

    # TODO : self.tiled instead of parameter in resize()

    def __init__(self, parent, image, pos=None, w=None, h=None, **kwargs):
        """
        Cree une image

        If w or h parameters are filled, width or height of image argument
        are respectively resized
        """

        assert isinstance(image, pygame.Surface), "image must be a Surface"

        image_size = image.get_size()
        if w is None: w = image_size[0]
        if h is None: h = image_size[1]
        if image_size != (w, h):
            surface = pygame.transform.scale(image, (w, h))
        else:
            surface = image.copy()

        ResizableWidget.__init__(
            self,
            parent=parent,
            surface=surface,
            pos=pos,
            **kwargs
        )

    def collidemouse_alpha(self):  # TODO
        pass

    def resize(self, w, h, tiled=False):

        if tiled:

            surface = pygame.Surface((w, h), pygame.SRCALPHA)
            surface.blit(self.surface, (0, 0))

            if w > self.w:
                for i in range(int(w / self.w)):
                    surface.blit(self.surface, (self.w * (i + 1), 0))

            if h > self.h:
                row = surface.subsurface((0, 0, w, self.h)).copy()
                for i in range(int(h / self.h)):
                    surface.blit(row, (0, self.h * (i + 1)))

            self.set_surface(surface)

        else:
            self.set_surface(pygame.transform.scale(self.surface, (w, h)))