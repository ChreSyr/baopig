
import pygame
from baopig.lib import Rectangle, Runable


class ProgressBar(Rectangle, Runable):

    def __init__(self, parent, min, max, get_progress, **kwargs):

        try: Rectangle.__init__(self, parent, **kwargs)
        except AttributeError:
            pass  # 'ProgressBar' object has no attribute '_progression'
        Runable.__init__(self, parent, **kwargs)

        # Non protected fields (don't need it)
        self.min = min
        self.max = max
        self.get_progress = get_progress
        # Protected field
        self._progression = 0  # percentage between 0 and 1

        self.set_border_color(2)  # TODO : style
        self.set_border_width((0, 0, 0))  # TODO : style
        self.run()
        self.start_running()

    progression = property(lambda self: self._progression)

    def paint(self):
        """
        If size is set, this method resizes the ProgressBar
        """
        # size = size if size is not None else self.size
        # surface = pygame.Surface(size, pygame.SRCALPHA)
        self.surface.fill((0, 0, 0, 0))
        pygame.draw.rect(self.surface, self.color, (0, 0, self.progression * self.w, self.h))
        pygame.draw.rect(self.surface, self.border_color, self.auto_hitbox, self.border_width * 2 - 1)
        # self.set_surface(surface)

    def run(self):
        self._progression = (float(self.get_progress()) - self.min) / (self.max - self.min)
        self.send_paint_request()
