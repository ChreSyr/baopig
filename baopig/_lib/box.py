

import pygame
from .utilities import MarginType, Color, paint_lock
from .layer import Layer
from .container import Container
from .image import Image


class BoxRect(pygame.Rect):

    def __init__(self, rect, margin, out=False):

        if out:
            pygame.Rect.__init__(
                self,
                rect.left - margin.left,
                rect.top - margin.top,
                rect.width + margin.left + margin.right,
                rect.height + margin.top + margin.bottom
            )
        else:
            pygame.Rect.__init__(
                self,
                rect.left + margin.left,
                rect.top + margin.top,
                rect.width - margin.left - margin.right,
                rect.height - margin.top - margin.bottom
            )


class Box(Container):

    STYLE = Container.STYLE.substyle()
    STYLE.create(
        margin = 0,
        border_width = 0,
        padding = 0,
        background_image = None
    )
    STYLE.set_type("margin", MarginType)
    STYLE.set_type("border_width", MarginType)
    STYLE.set_type("padding", MarginType)

    # NOTE : if width or height is defined in style, and a background_image is set,
    # the width and height values will be ignored

    def __init__(self, parent, **options):

        self.inherit_style(parent, options)  # TODO : **options ?

        Container.__init__(self, parent, **options)

        self._margin = self.style["margin"]
        self._border = self.style["border_width"]
        self._padding = self.style["padding"]
        self.background_layer = None
        self._background_ref = lambda: None

        self.connect("handle_resize", self.signal.RESIZE)
        background_image = self.style["background_image"]
        if background_image is not None:
            self.set_background_image(background_image)
            return
            if self.style["width"] is None:
                self.style.modify(width=background_image.get_width())
            if self.style["height"] is None:
                self.style.modify(height=background_image.get_height())

    background = property(lambda self: self._background_ref())
    border = property(lambda self: self._border)
    border_rect = property(lambda self: self.rect)
    content_rect = property(lambda self: BoxRect(self.padding_rect, self.padding))
    margin = property(lambda self: self._margin)
    margin_rect = property(lambda self: BoxRect(self.rect, self.margin, out=True))
    padding = property(lambda self: self._padding)
    padding_rect = property(lambda self: BoxRect(self.rect, self.border))

    def handle_resize(self, old_size):

        if self.background is not None:
            self.background.resize(*self.size)

    def set_background_image(self, surf, background_adapt=True):
        """
        If background_adapt is True, the surf adapts to the zone's size
        Else, the zone's size adapts to the background_image
        """
        if surf is None:
            if self.background is not None:
                with paint_lock:
                    self.background.kill()
            return
        if background_adapt and surf.get_size() != self.size:
            surf = pygame.transform.scale(surf, self.size)
        if self.background_layer is None:
            self.background_layer = Layer(self, Image, name="background_layer", level=self.layers_manager.BACKGROUND)
        with paint_lock:
            if self.background is not None:
                self.background.kill()
                assert self.background is None
            self._background_ref = Image(self, surf, pos=(0, 0), layer=self.background_layer).get_weakref()
            if background_adapt is False:
                self.resize(*self.background.size)

            def handle_background_kill(weakref):
                if weakref is self._background_ref:
                    self._background_ref = lambda: None
            self.background.signal.KILL.connect(handle_background_kill)
