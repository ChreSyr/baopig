import pygame
from baopig.pybao.objectutilities import Object
from baopig.lib import Focusable, Layer, Validable
from baopig.lib import Rectangle, Image, Container
from .text import Text


class AButton_DisableSail(Rectangle):
    STYLE = Rectangle.STYLE.substyle()
    STYLE.modify(width="100%", height="100%", color=(255, 255, 255, 128))

    def __init__(self, abutton):
        Rectangle.__init__(self, abutton, visible=False, layer=abutton.above_content)


class AButton_FocusSail(Rectangle):
    STYLE = Rectangle.STYLE.substyle()
    STYLE.modify(width="100%", height="100%", color=(0, 0, 0, 0), border_color="theme-color-border", border_width=1)

    def __init__(self, abutton):
        Rectangle.__init__(self, abutton, visible=False, layer=abutton.behind_content)


class AButton_HoverSail(Rectangle):
    STYLE = Rectangle.STYLE.substyle()
    STYLE.modify(width="100%", height="100%")
    STYLE.create(alpha=63)

    def __init__(self, abutton):
        Rectangle.__init__(self, abutton, visible=False, layer=abutton.above_content)
        self.set_color((0, 0, 0, self.style["alpha"]))


class AButton_LinkSail(Rectangle):
    STYLE = Rectangle.STYLE.substyle()
    STYLE.modify(width="100%", height="100%")
    STYLE.create(alpha=63)

    def __init__(self, abutton):
        Rectangle.__init__(self, abutton, visible=False, layer=abutton.behind_content)
        self.set_color((0, 0, 0, self.style["alpha"]))


class AbstractButton(Container, Focusable, Validable):
    """
    Abstract button

    A button is clicked when the link is released while the mouse is still
    hovering it (for more explanations about links, see LinkableByMouse)

    - background color
    - focus
    - link
    - text
    - hover
    """

    STYLE = Container.STYLE.substyle()
    STYLE.modify(
        width=100,
        height=35,
        background_color="theme-color-content",
        padding=10,
    )
    STYLE.create(
        catching_errors=False,
        disable_class=AButton_DisableSail,
        focus_class=AButton_FocusSail,
        hover_class=AButton_HoverSail,
        link_class=AButton_LinkSail,
    )

    def __init__(self, parent, command=None, hover=None, link=None, focus=None, **kwargs):

        Container.__init__(self, parent, **kwargs)
        Focusable.__init__(self, parent, **kwargs)
        Validable.__init__(self, catching_errors=self.style["catching_errors"])

        if command is None:
            self.command = lambda: None
        else:
            self.command = command  # non protected field
            assert callable(command), "command must be callable"

        self.behind_content = Layer(self, weight=0)
        self.content = Layer(self, weight=1)
        self.above_content = Layer(self, weight=2)

        void = Object(show=lambda: None, hide=lambda: None)

        self.set_style_for(Rectangle, width="100%", height="100%")  # TODO : remove this in AButton_Sail.STYLE
        self.set_style_for(Image, width="100%", height="100%")  # TODO : implement ? (this is not working)

        hover_class = self.style["hover_class"]
        if hover_class:
            self._hover_sail_ref = hover_class(self).get_weakref()
        else:
            self._hover_sail_ref = lambda: void

        focus_class = self.style["focus_class"]
        if focus_class:
            self._focus_sail_ref = focus_class(self).get_weakref()
        else:
            self._focus_sail_ref = lambda: void

        link_class = self.style["link_class"]
        if link_class:
            self._link_sail_ref = link_class(self).get_weakref()
        else:
            self._link_sail_ref = lambda: void

        disable_class = self.style["disable_class"]
        if disable_class:
            self._disable_sail_ref = disable_class(self).get_weakref()
        else:
            self._disable_sail_ref = lambda: void

        if isinstance(hover, int) and hover != -1:  # TODO : hover_alpha=False or Sail
            # Adapts the hover sail to the surface -> alpha pixels are not hovered
            hidden = self.is_hidden
            if hidden:
                if self.has_locked("visibility"):
                    raise NotImplementedError
                self.show()
            self._flip_without_update()
            if hidden:
                self.hide()
            self.hover_sail.surface.blit(self.surface, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)

        self.signal.KILL.connect(self.handle_kill, owner=None)

    disable_sail = property(lambda self: self._disable_sail_ref())
    focus_sail = property(lambda self: self._focus_sail_ref())
    hover_sail = property(lambda self: self._hover_sail_ref())
    link_sail = property(lambda self: self._link_sail_ref())

    def disable(self):

        self.set_touchable_by_mouse(False)

    def enable(self):

        self.set_touchable_by_mouse(True)

    def handle_defocus(self):

        self.focus_sail.hide()

    def handle_focus(self):

        self.focus_sail.show()

    def handle_hover(self):

        self.hover_sail.show()

    def handle_keydown(self, key):

        if key == pygame.K_RETURN:
            self.validate()
            self.link_sail.show()
        else:
            super().handle_keydown(key)

    def handle_keyup(self, key):

        if key == pygame.K_RETURN:
            self.link_sail.hide()  # For validation via RETURN key

    def handle_kill(self):

        void = Object(show=lambda: None, hide=lambda: None)
        self._link_sail_ref = lambda: void

    def handle_link(self):

        self.link_sail.show()

    def handle_unhover(self):

        self.hover_sail.hide()

    def handle_unlink(self):
        # TODO : test : if a linked Clickable is hidden, handle_unlink() is called but validate() is not called

        if self.collidemouse():
            self.validate()

        self.link_sail.hide()

    def handle_validate(self):

        self.command()

    def set_touchable_by_mouse(self, val):

        super().set_touchable_by_mouse(val)

        if self.is_touchable_by_mouse:
            self.disable_sail.hide()
        else:
            self.disable_sail.show()


class Button_Text(Text):
    STYLE = Text.STYLE.substyle()
    STYLE.modify(
        align_mode="left",
        loc="center",
        refloc="center",
    )

    def __init__(self, button, text, **kwargs):

        assert isinstance(button, AbstractButton)

        Text.__init__(self, button, text=text, selectable=False, **kwargs)

        assert self.width_is_adaptable

        content_rect = button.content_rect
        if content_rect.height < self.font.height:
            self.font.config(height=content_rect.height)  # changing the font will automatically update the text
        while self.rect.width > content_rect.width or self.rect.height > content_rect.height:
            if self.font.height == 2:
                break
                # raise ValueError(f"This text is too long for the text area : {text} (area={content_rect})")
            self.font.config(height=self.font.height - 1)  # changing the font will automatically update the text
        # if self.rect.height > content_rect.height:
        #     self.resize_height(content_rect.height)


class Button(AbstractButton):
    """
    Un Button est un bouton classique, avec un text
    Sa couleur d'arriere plan par defaut est (64, 64, 64)
    """

    STYLE = AbstractButton.STYLE.substyle()
    STYLE.create(
        text_class=Button_Text,
        text_style={},
    )
    STYLE.set_constraint("text_class", lambda val: issubclass(val, Button_Text))

    text = property(lambda self: self.text_widget.text)

    def __init__(self, parent, text=None, **kwargs):

        AbstractButton.__init__(self, parent, **kwargs)

        if text is not None:
            assert isinstance(text, str)
            self.text_widget = self.style["text_class"](self, text=text, layer=self.content, **self.style["text_style"])
            if self.name == "NoName":
                self._name = text
