
import pygame
from baopig._lib import Rectangle, Runable


class ProgressBar(Rectangle, Runable):

    def __init__(self, parent, min, max, get_progress, *args, **kwargs):

        try: Rectangle.__init__(self, parent, *args, **kwargs)
        except AttributeError: pass  # 'ProgressBar' object has no attribute '_progression'
        Runable.__init__(self)

        # Non protected fields (don't need it)
        self.min = min
        self.max = max
        self.get_progress = get_progress
        # Protected field
        self._progression = 0  # percentage between 0 and 1

        self.set_border((0, 0, 0), 2)  # TODO : ressource
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
        pygame.draw.rect(self.surface, self.color, (0, 0, self.progression * size[0], size[1]))
        pygame.draw.rect(self.surface, self.border_color, (self.auto_hitbox), self.border_width * 2 - 1)
        # self.set_surface(surface)

    def run(self):
        self._progression = (float(self.get_progress()) - self.min) / (self.max - self.min)
        self.send_paint_request()
