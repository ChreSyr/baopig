
import pygame
from .textedit import TextEdit


class LineEdit(TextEdit):
    """
    LineEdit is a Text who only contains 1 line
    """

    def handle_keydown(self, key):

        if key == pygame.K_RETURN:
            self.defocus()
        else:
            super().handle_keydown(key)

    def set_text(self, text):

        if '\n' in text:
            raise PermissionError("A LineEdit cannot contain a backslash")
        else:
            super().set_text(text)
