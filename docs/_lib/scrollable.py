

import time
from pygame import Rect
from baopig.io import mouse
from .hoverable import Hoverable
from .container import Container


class Scrollable(Hoverable):
    """If the widget is hovered and the mouse is scrolling, scroll

    scrollaxis is one of '', 'x', 'y', 'xy'

    The scroll is between window and rect
    You should write
        scrollable_widget.set_window(something)

    """

    def __init__(self, scrollaxis=None):

        assert isinstance(self, Container)
        if scrollaxis is None:
            scrollaxis = "y"
        assert scrollaxis in ("", "x", "y", "xy")
        self._scrollaxis = scrollaxis

    scrollaxis = property(lambda self: self._scrollaxis)

    def scroll(self, dx, dy):

        assert self.window is not None
        window = Rect(self.window)

        if dx < 0:
            right = self.right + dx
            if window.right > right:
                dx = window.right - self.right
        elif dx > 0:
            left = self.left + dx
            if window.left < left:
                dx = window.left - self.left

        if dy < 0:
            bottom = self.bottom + dy
            if window.bottom > bottom:
                dy = window.bottom - self.bottom
        elif dy > 0:
            top = self.top + dy
            if window.top < top:
                dy = window.top - self.top

        if (dx == 0) and (dy == 0):
            return

        self.move(dx, dy)


class ScrollableByMouse(Scrollable, Hoverable):

    def __init__(self, scrollaxis=None):

        Scrollable.__init__(self, scrollaxis)
        Hoverable.__init__(self)

        self._last_scroll_time = time.time()  # for faster scroll when together
        self.connect("handle_mouse_scroll", mouse.signal.SCROLL)

    def handle_mouse_scroll(self, scroll_event):
        """
        WARNING : this is not properly coded.
        If this widget contains a Scrollable widget, both can scroll together
        If a widget is hovering this one, it still can be scrolled
        """

        if self.window is None: return
        if not self.collidemouse(): return
        accelerator = 1
        old_scroll_time = self._last_scroll_time
        self._last_scroll_time = time.time()
        d = self._last_scroll_time - old_scroll_time

        if d < 0.5:
            accelerator = 20
        elif d < 0.1:
            accelerator = 5

        if "y" in self.scrollaxis:
            self.scroll(0, scroll_event.direction * accelerator)
        else:
            self.scroll(scroll_event.direction * accelerator, 0)
