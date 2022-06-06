
import pygame
from baopig.pybao.issomething import *
from baopig.ressources import *
from baopig.font import Font
from baopig.io import keyboard
from baopig._lib import ApplicationExit, Clickable, Layer
from baopig._lib import Widget, Container, Sail, Image, Box, Hoverable
from .label import Label
from .text import TextLabel, Text


class AbstractButton2(Label, Clickable, Hoverable):
    """
    Abstract button

    - background color
    - focus
    - link
    - text
    - hover
    """

    STYLE = Label.STYLE.substyle()
    STYLE.modify(
        background_color = "theme-color-content"
    )
    STYLE.create(
        catching_errors = False,
    )

    def __init__(self, parent, command=None, font=None, size=None, margin=None, name=None,
                 background_color=None, catching_errors=None, hover=None, link=None, focus=None, **kwargs):

        self.inherit_style(parent, background_color=background_color, catching_errors=catching_errors)

        if margin is None: margin = 5
        if command is None: command = lambda: None
        # if name is None: name = "<{}({})>".format(self.__class__.__name__, text)

        assert callable(command), "command must be callable"

        Label.__init__(
            self,
            parent=parent,
            text=text,
            font=font,
            size=size,
            margin=margin,  # TODO : padding instead of margin
            text_location="center",
            selectable=False,
            name=name,
            **kwargs
        )
        Hoverable.__init__(self)
        Clickable.__init__(self, catching_errors=self.style["catching_errors"])

        self.command = command  # non protected field
        self._hover_sail_ref = lambda: None
        self._link_sail_ref = lambda: None
        self._focus_rect_ref = lambda: None
        Layer(self, name="nontouchable_layer", touchable=False)
        self.text_component.swap_layer("nontouchable_layer")

        if hover != -1:
            if hover is None:
                self._hover_sail_ref = Sail(
                    parent=self,
                    color=(0, 0, 0, 63),
                    pos=(0, 0),
                    size=self.size,
                    name=self.name+".hover_sail",
                ).get_weakref()
            else:
                self._hover_sail_ref = Image(
                    self, hover, layer="nontouchable_layer", name=self.name+".hover_sail"
                ).get_weakref()
            self.hover_sail.hide()
            self.hover_sail.connect("show", self.signal.HOVER)
            self.hover_sail.connect("hide", self.signal.UNHOVER)

        if focus != -1:
            if focus is None:
                self._focus_rect_ref = Sail(  # TODO : rethink objects with widgets philosophy (everything's a widget)
                    parent=self,
                    color=(0, 0, 0, 0),
                    pos=(0, 0),  # (half_margin_left, half_margin_top),
                    size=self.size,  # (self.w - half_margin_left - half_margin_right, self.h - half_margin_top - half_margin_bottom),
                    name=self.name + ".focus_rect"
                ).get_weakref()
                self.focus_rect.set_border(color=(0, 0, 0), width=1)  # TODO : Border
            else:
                self._focus_rect_ref = Image(
                    self, focus, layer="nontouchable_layer", name=self.name+".focus_sail"
                ).get_weakref()
            self.focus_rect.hide()
            self.focus_rect.connect("show", self.signal.FOCUS)
            self.focus_rect.connect("hide", self.signal.DEFOCUS)
            self.focus_rect.move_behind(self.text_component)

        if link != -1:
            if link is None:
                self._link_sail_ref = Sail(
                    parent=self,
                    color=(0, 0, 0, 63),
                    pos=(0, 0),
                    size=self.size,
                    name=self.name+".link_sail",
                ).get_weakref()
            else:
                self._link_sail_ref = Image(
                    self, link, layer="nontouchable_layer", name=self.name+".link_sail"
                ).get_weakref()
            self.link_sail.hide()
            self.link_sail.connect("show", self.signal.LINK)
            self.link_sail.connect("hide", self.signal.UNLINK)
            self.link_sail.move_behind(self.text_component)

        self._disable_sail_ref = Sail(  # TODO : same as hover, focus and link
            parent=self,
            color=(255, 255, 255, 128),
            pos=(0, 0),
            size=self.size,
            name=self.name + ".disable_sail"
        ).get_weakref()
        self.disable_sail.hide()

    disable_sail = property(lambda self: self._disable_sail_ref())
    focus_rect = property(lambda self: self._focus_rect_ref())
    hover_sail = property(lambda self: self._hover_sail_ref())
    link_sail = property(lambda self: self._link_sail_ref())

    def enable(self):

        self.disable_sail.hide()
        self.hover_sail.lock_visibility(locked=False)
        if self.is_hovered:
            self.hover_sail.show()

    def disable(self):

        self.disable_sail.show()
        self.hover_sail.hide()
        self.hover_sail.lock_visibility(locked=True)
        self.hover_sail.show()
        assert not self.hover_sail.is_visible

    def handle_keydown(self, key):

        if key is keyboard.RETURN:
            self.link_sail.show()
            self.validate()
        elif key is keyboard.TAB:
            self.focus_next()
        elif key in (keyboard.RIGHT, keyboard.DOWN):
            self.focus_next()
        elif key in (keyboard.LEFT, keyboard.UP):
            self.focus_antecedant()
        # TODO : arrows can swap to next focusables

    def handle_keyup(self, key):

        if key is keyboard.RETURN:
            self.link_sail.hide()

    def validate(self, *args, **kwargs):

        self.command(*args, **kwargs)


class ButtonText(Text):  # TODO : das is das ?

    STYLE = Text.STYLE.substyle()
    STYLE.modify(
        align_mode = "left",
    )

    def __init__(self, button, text, **options):

        assert isinstance(button, AbstractButton)
        assert '\n' not in text
        self.inherit_style(button, **options)
        content_rect = button.content_rect

        if content_rect.height < self.style["font_height"]:
            self.style.modify(font_height=content_rect.height)
            # raise ValueError("This text has a too high font for the text area : "
            #                  f"{self.style['font_height']} (maximum={content_rect.height})")
        Text.__init__(
            self, button,
            text=text,
            sticky="center",
            selectable=False,
            **options
        )
        while self.width > content_rect.width:
            if self.font.height == 2:
                raise ValueError(f"This text is too long for the text area : {text} (area={content_rect}), {self.align_mode}, {self.width}")
            self.font.config(height=self.font.height - 1)  # changing the font will automatically update the text


class AbstractButton(Box, Clickable, Hoverable):
    """
    Abstract button

    - background color
    - focus
    - link
    - text
    - hover
    """

    STYLE = Box.STYLE.substyle()
    STYLE.modify(
        width=100,
        height=35,
        background_color = "theme-color-content",
        padding=10,
    )
    STYLE.create(
        catching_errors = False,
    )

    def __init__(self, parent, command=None, name=None,
                 background_color=None, catching_errors=None, hover=None, link=None, focus=None, **options):

        self.inherit_style(parent, options, background_color=background_color, catching_errors=catching_errors)

        if command is None: command = lambda: None

        assert callable(command), "command must be callable"

        Box.__init__(
            self,
            parent=parent,
            name=name,
            **options
        )
        Hoverable.__init__(self)
        Clickable.__init__(self, catching_errors=self.style["catching_errors"])

        self.connect("press", self.signal.LINK)
        self.connect("unpress", self.signal.UNLINK)  # TODO : only self.signal.THING.connect(function)

        self.command = command  # non protected field

        if self.default_layer is None:
            self.layers_manager.create_temporary_layer()
        self.behind_lines = Layer(self, weight=self.default_layer.weight-1)
        self.above_lines = Layer(self, weight=self.default_layer.weight+1)

        self._hover_sail_ref = lambda: None
        self._link_sail_ref = lambda: None
        self._focus_rect_ref = lambda: None
        # Layer(self, name="nontouchable_layer", touchable=False)
        # self.text_component.swap_layer("nontouchable_layer")

        if hover != -1:
            if hover is None: hover = 63
            if isinstance(hover, int):
                self._hover_sail_ref = Sail(
                    parent=self,
                    color=(0, 0, 0, hover),
                    pos=(0, 0),
                    size=self.size,
                    name=self.name+".hover_sail",
                ).get_weakref()
            else:
                self._hover_sail_ref = Image(
                    self, hover, layer="nontouchable_layer", name=self.name+".hover_sail"
                ).get_weakref()
            self.hover_sail.hide()
            self.hover_sail.connect("show", self.signal.HOVER)
            self.hover_sail.connect("hide", self.signal.UNHOVER)
            self.hover_sail.swap_layer(self.above_lines)

        if focus != -1:
            if focus is None:
                self._focus_rect_ref = Sail(
                    parent=self,
                    color=(0, 0, 0, 0),
                    pos=(0, 0),  # (half_margin_left, half_margin_top),
                    size=self.size,  # (self.w - half_margin_left - half_margin_right, self.h - half_margin_top - half_margin_bottom),
                    border_color="theme-color-border",
                    border_width=1,
                    name=self.name + ".focus_rect"
                ).get_weakref()
                # self.focus_rect.set_border(color=, width=1)  # TODO : Border
            else:
                self._focus_rect_ref = Image(
                    self, focus, layer="nontouchable_layer", name=self.name+".focus_sail"
                ).get_weakref()
            self.focus_rect.hide()
            self.focus_rect.connect("show", self.signal.FOCUS)
            self.focus_rect.connect("hide", self.signal.DEFOCUS)
            self.focus_rect.swap_layer(self.behind_lines)

        if link != -1:
            if link is None:
                self._link_sail_ref = Sail(
                    parent=self,
                    color=(0, 0, 0, 63),
                    pos=(0, 0),
                    size=self.size,
                    name=self.name+".link_sail",
                ).get_weakref()
            else:
                self._link_sail_ref = Image(
                    self, link, layer="nontouchable_layer", name=self.name+".link_sail"
                ).get_weakref()
            self.link_sail.hide()
            self.link_sail.connect("show", self.signal.LINK)
            self.link_sail.connect("hide", self.signal.UNLINK)
            self.link_sail.swap_layer(self.behind_lines)

        self._disable_sail_ref = Sail(  # TODO : same as hover, focus and link
            parent=self,
            color=(255, 255, 255, 128),
            pos=(0, 0),
            size=self.size,
            name=self.name + ".disable_sail"
        ).get_weakref()
        self.disable_sail.hide()
        self.disable_sail.swap_layer(self.above_lines)

        if isinstance(hover, int) and hover != -1:
            hidden = self.is_hidden
            if hidden:
                if self.has_locked.visibility:
                    raise NotImplementedError
                self.show()
            self.paint()  # cannot paint if not visible
            if hidden:
                self.hide()
            self.hover_sail.surface.blit(self.surface, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

    disable_sail = property(lambda self: self._disable_sail_ref())
    focus_rect = property(lambda self: self._focus_rect_ref())
    hover_sail = property(lambda self: self._hover_sail_ref())
    link_sail = property(lambda self: self._link_sail_ref())

    def enable(self):

        self.disable_sail.hide()
        self.hover_sail.lock_visibility(locked=False)
        if self.is_hovered:
            self.hover_sail.show()

    def disable(self):

        self.disable_sail.show()
        self.hover_sail.hide()
        self.hover_sail.lock_visibility(locked=True)
        self.hover_sail.show()
        assert not self.hover_sail.is_visible

    def handle_keydown(self, key):

        if key is keyboard.RETURN:
            self.link_sail.show()
            self.validate()
        elif key is keyboard.TAB:
            self.focus_next()
        elif key in (keyboard.RIGHT, keyboard.DOWN):
            self.focus_next()
        elif key in (keyboard.LEFT, keyboard.UP):
            self.focus_antecedant()
        # TODO : arrows can swap to next focusable

    def handle_keyup(self, key):

        if key is keyboard.RETURN:
            self.link_sail.hide()

    def press(self):
        """Stuff to do when the button is pressed"""

    def unpress(self):
        """Stuff to do when the button is unpressed"""

    def validate(self, *args, **kwargs):

        self.command(*args, **kwargs)


class Button(AbstractButton):
    """
    Un Button est un bouton classique, avec un text
    Sa couleur d'arriere plan par defaut est (64, 64, 64)
    """

    STYLE = AbstractButton.STYLE.substyle()
    STYLE.create(
        text_class = ButtonText,
        text_style = {},
    )
    STYLE.set_constraint("text_class", lambda val: issubclass(val, ButtonText))

    def __init__(self, parent, text=None,
                 command=None, background_color=None, **kwargs):

        AbstractButton.__init__(
            self,
            parent=parent,
            command=command,
            background_color=background_color,
            **kwargs
        )
        if text is not None:
            assert isinstance(text, str)
            self.text_widget = self.style["text_class"](self, text=text, **self.style["text_style"])
            if self.name == "NoName": self._name = text

    def copy(self):

        return Button(
            parent=self.parent,
            text=self.text,
            pos=self.pos,
            w=self.w,
            h=self.h,
            margin=0,  # TODO : self.margin
            font_size=self.font_size,
            font_color=self.font_color,
            command=self.command,
            background_color=self.background.color,
            name="Copied"+self.name
        )

