
import pygame
from .textedit import TextEdit


class LineEdit(TextEdit):
    """
    LineEdit is a Text who only contains 1 line
    """
    # TODO : a lot of reworks and unit tests
    # TODO : LineEdit.line instead of .lines ?

    # def __init__(self, *args, **kwargs):

    #     TextEdit.__init__(self, *args, **kwargs)

    def handle_keydown(self, key):

        if key == pygame.K_RETURN:
            self.defocus()
        else:
            super().handle_keydown(key)
