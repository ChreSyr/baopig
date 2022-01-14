

import pygame
from baopig._lib import Clickable, Hoverable
from baopig._lib import Rectangle
from .button import Button, ButtonText


class CheckMark(Rectangle):

    STYLE = Rectangle.STYLE.substyle()
    STYLE.modify(
        height=7,
        width=7,
        color="theme-color-border"
    )

    def __init__(self, checkbox):

        # mid = checkbox.height / 2
        Rectangle.__init__(self, checkbox, pos=(0, 0), pos_location="center",
                           pos_ref=checkbox.checkmarkframe, pos_ref_location="center")


class CheckMarkFrame(Rectangle):

    STYLE = Rectangle.STYLE.substyle()
    STYLE.modify(
        height=15,
        width=15,
        border_width=2,
        color=(0, 0, 0, 0)
    )

    def __init__(self, checkbox):

        mid = checkbox.height / 2
        Rectangle.__init__(self, checkbox, pos=(checkbox.padding.left, mid), pos_location="midleft")


class CheckBox(Button):
    # NOTE : connect a function to any state change with the VALIDATE signal

    STYLE = Button.STYLE.substyle()
    STYLE.modify(
        width=100,
        height=35,
        background_color = (0, 0, 0, 0),
        text_style = {"font_height": 15},
        padding=5
    )
    # TODO : rework checkbox's margin padding and this kind of stuff
    STYLE.create(
        checkmark_class = CheckMark,
        checkmarkframe_class = CheckMarkFrame
    )

    def __init__(self, parent, text=None, is_selected=False, **kwargs):

        Button.__init__(
            self, parent, text=text, **kwargs
        )

        self._is_selected = is_selected

        self._checkmarkframe_ref = CheckMarkFrame(self).get_weakref()
        self._checkmark_ref = CheckMark(self).get_weakref()

        self.checkmark.hide()

        # TODO : all of this, rework with better padding and margin management
        # TODO : when the text is too long, and the width is not specified, the box is lengthen

        # Sliding the text to the right
        assert self.w > self.h
        self.text_widget.center = ((self.w + self.checkmarkframe.right) / 2, self.h / 2)
        area = pygame.Rect(self.content_rect)
        area_end = area.right
        area.left = self.checkmarkframe.right + self.checkmarkframe.left
        area.w = area_end - area.left
        while self.text_widget.w > area.w:
            if self.text_widget.font.height == 2:
                raise ValueError(f"This text is too long for the text area : {text} (area={rect})")
            self.text_widget.font.config(height=self.text_widget.font.height - 1)

    checkmark = property(lambda self: self._checkmark_ref())
    checkmarkframe = property(lambda self: self._checkmarkframe_ref())
    is_selected = property(lambda self: self._is_selected)

    def validate(self, *args, **kwargs):

        self._is_selected = not self.is_selected

        if self.is_selected is True:
            self.checkmark.show()
        else:
            self.checkmark.hide()

        self.command(*args, **kwargs)

        return self.is_selected
