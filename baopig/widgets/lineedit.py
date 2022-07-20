
import pygame
from .textedit import TextEdit


class LineEdit(TextEdit):
    """
    LineEdit is a TextEdit who only contains 1 line
    """

    def __init__(self, parent, **kwargs):

        TextEdit.__init__(self, parent, **kwargs)
        self.x_scroller.hide()
        self.x_scroller.set_lock(visibility=True)

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
