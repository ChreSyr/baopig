
import pygame
from .textedit import TextEdit


class LineEdit(TextEdit):  # TODO : mouse's double click at text_widget's right -> select the text
    """
    LineEdit is a TextEdit who only contains 1 line
    """
    STYLE = TextEdit.STYLE.substyle()
    STYLE.modify(
        height=0
    )

    def __init__(self, parent, **kwargs):

        TextEdit.__init__(self, parent, **kwargs)

        assert self.rect.height == 0, "Cannot set a height, LineEdit manages its height itself"

        self.x_scroller.hide()
        self.x_scroller.set_lock(visibility=True)
        self.resize_height(self.padding.top + self.text_widget.rect.height + self.padding.bottom)

        assert self.y_scroller.is_hidden

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
