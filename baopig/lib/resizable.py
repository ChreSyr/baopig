

import pygame
from .widget import Widget


class ResizableWidget(Widget):
    """Class for widgets who can be resized"""

    STYLE = Widget.STYLE.substyle()
    STYLE.create(
        width=None,  # must be filled
        height=None,  # must be filled
    )

    def __init__(self, parent, size=None, **kwargs):
        """NOTE : can be size=(50, 45) or width=50, height=45"""

        self.inherit_style(parent, options=kwargs)

        if size is None:
            self._asked_size = self.style["width"], self.style["height"]
        else:
            self._asked_size = size

        if "surface" not in kwargs:
            kwargs["surface"] = pygame.Surface(self._get_asked_size(), pygame.SRCALPHA)

        Widget.__init__(self, parent, **kwargs)

        self.signal.RESIZE.connect(self.handle_resize, owner=None)
        self.origin.reference.signal.RESIZE.connect(self._update_size, owner=self)

    def _get_asked_size(self):

        size = self._asked_size
        with_percentage = False
        for coord in size:
            if isinstance(coord, str):
                # hard stuff
                assert coord[-1] == '%', size
                with_percentage = True
            else:
                assert isinstance(coord, (int, float)), f"Wrong value in size : {coord} (must be a number)"
                assert coord >= 0, f"Wrong value in size : {coord} (must be positive)"

        if with_percentage:
            size = list(size)
            for i, coord in enumerate(size):
                if isinstance(coord, str):
                    size[i] = self.parent.size[i] * int(coord[:-1]) / 100

        return size

    def _update_size(self):

        asked_size = self._asked_size
        self.resize(*self._get_asked_size())
        self._asked_size = asked_size

    def handle_resize(self):
        """Stuff to do when the widget is resized"""

    def resize(self, w, h):
        """Sets up the new component's surface"""

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

        self.set_surface(pygame.Surface(asked_size, pygame.SRCALPHA))

    def resize_height(self, h):

        self.resize(self._asked_size[0], h)

    def resize_width(self, w):

        self.resize(w, self._asked_size[1])
