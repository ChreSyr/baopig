
import pygame
from baopig.lib import Rectangle, Runable


class ProgressBar(Rectangle, Runable):  # TODO : tests & documentation
    STYLE = Rectangle.STYLE.substyle()
    STYLE.modify(
        border_width=2
    )

    def __init__(self, parent, minval, maxval, get_progress, **kwargs):

        try:
            Rectangle.__init__(self, parent, **kwargs)
        except AttributeError:
            pass  # 'ProgressBar' object has no attribute '_progression'
        Runable.__init__(self, parent, **kwargs)

        # Non protected fields (don't need it)
        self._minval = minval
        self._maxval = maxval
        self.get_progress = get_progress
        # Protected field
        self._progression = 0  # percentage between 0 and 1

        self.run()
        self.set_running(True)

    progression = property(lambda self: self._progression)

    def paint(self):
        self.surface.fill((0, 0, 0, 0))
        pygame.draw.rect(self.surface, self.color, (0, 0, self.progression * self.rect.w, self.rect.h))
        pygame.draw.rect(self.surface, self.border_color, self.auto_hitbox, self.border_width * 2 - 1)

    def run(self):
        self._progression = (float(self.get_progress()) - self._minval) / (self._maxval - self._minval)
        self.send_paint_request()
