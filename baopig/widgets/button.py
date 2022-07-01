import pygame
from baopig.lib import Clickable, Layer
from baopig.lib import Sail, Image, Container, Hoverable
from .text import Text


class ButtonText(Text):
    STYLE = Text.STYLE.substyle()
    STYLE.modify(
        align_mode="left",
        pos_location="center",
        pos_ref_location="center",
    )

    def __init__(self, button, text, **options):

        assert isinstance(button, AbstractButton)
        self.inherit_style(button, options=options)
        content_rect = button.content_rect

        if content_rect.height < self.style["font_height"]:
            self.style.modify(font_height=content_rect.height)
            # raise ValueError("This text has a too high font for the text area : "
            #                  f"{self.style['font_height']} (maximum={content_rect.height})")
        Text.__init__(
            self, button,
            text=text,
            selectable=False,
            **options
        )

        while self.width > content_rect.width:
            if self.font.height == 2:
                raise ValueError(f"This text is too long for the text area : {text} (area={content_rect})")
            self.font.config(height=self.font.height - 1)  # changing the font will automatically update the text
        if self.height > content_rect.height:
            self.resize_height(content_rect.height)


class AbstractButton(Container, Clickable, Hoverable):
    """
    Abstract button

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
    )

    def __init__(self, parent, command=None, name=None,
                 background_color=None, catching_errors=None, hover=None, link=None, focus=None, **options):

        self.inherit_style(parent, options, background_color=background_color, catching_errors=catching_errors)

        if command is None:
            command = lambda: None

        assert callable(command), "command must be callable"

        Container.__init__(self, parent=parent, name=name, **options)
        Hoverable.__init__(self, parent)
        Clickable.__init__(self, parent, catching_errors=self.style["catching_errors"])

        self.command = command  # non protected field

        if self.default_layer is None:
            Layer(self)  # TODO : usefull ?
        self.behind_lines = Layer(self, weight=self.default_layer.weight - 1)
        self.above_lines = Layer(self, weight=self.default_layer.weight + 1)

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
                    name=self.name + ".hover_sail",
                ).get_weakref()
            else:
                self._hover_sail_ref = Image(
                    self, hover, layer="nontouchable_layer", name=self.name + ".hover_sail"
                ).get_weakref()
            self.hover_sail.hide()
            self.signal.HOVER.connect(self.hover_sail.show, owner=self.hover_sail)
            self.signal.UNHOVER.connect(self.hover_sail.hide, owner=self.hover_sail)
            self.hover_sail.swap_layer(self.above_lines)

        if focus != -1:
            if focus is None:
                self._focus_rect_ref = Sail(
                    parent=self,
                    color=(0, 0, 0, 0),
                    pos=(0, 0),  # (half_margin_left, half_margin_top),
                    size=self.size,
                    border_color="theme-color-border",
                    border_width=1,
                    name=self.name + ".focus_rect"
                ).get_weakref()
                # self.focus_rect.set_border(color=, width=1)  # TODO : Border
            else:
                self._focus_rect_ref = Image(
                    self, focus, layer="nontouchable_layer", name=self.name + ".focus_sail"
                ).get_weakref()
            self.focus_rect.hide()
            self.signal.FOCUS.connect(self.focus_rect.show, owner=self.focus_rect)
            self.signal.DEFOCUS.connect(self.focus_rect.hide, owner=self.focus_rect)
            self.focus_rect.swap_layer(self.behind_lines)

        if link != -1:
            if link is None:
                self._link_sail_ref = Sail(
                    parent=self,
                    color=(0, 0, 0, 63),
                    pos=(0, 0),
                    size=self.size,
                    name=self.name + ".link_sail",
                ).get_weakref()
            else:
                self._link_sail_ref = Image(
                    self, link, layer="nontouchable_layer", name=self.name + ".link_sail"
                ).get_weakref()
            self.link_sail.hide()
            self.signal.LINK.connect(self.link_sail.show, owner=self.link_sail)
            self.signal.VALIDATE.connect(self.link_sail.show, owner=self.link_sail)  # For RETURN validation
            self.signal.UNLINK.connect(self.link_sail.hide, owner=self.link_sail)
            self.link_sail.swap_layer(self.behind_lines)  # TODO : layer=self.behind_lines

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

    def handle_enable(self):

        self.disable_sail.hide()
        self.hover_sail.lock_visibility(locked=False)
        if self.is_hovered:
            self.hover_sail.show()

    def handle_disable(self):

        self.disable_sail.show()
        self.hover_sail.hide()
        self.hover_sail.lock_visibility(locked=True)
        self.hover_sail.show()
        assert not self.hover_sail.is_visible

    def handle_keyup(self, key):

        if key == pygame.K_RETURN:
            self.link_sail.hide()

    def handle_validate(self):

        self.command()


class Button(AbstractButton):
    """
    Un Button est un bouton classique, avec un text
    Sa couleur d'arriere plan par defaut est (64, 64, 64)
    """

    STYLE = AbstractButton.STYLE.substyle()
    STYLE.create(
        text_class=ButtonText,
        text_style={},
    )
    STYLE.set_constraint("text_class", lambda val: issubclass(val, ButtonText))

    text = property(lambda self: self.text_widget.text)

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
            if self.name == "NoName":
                self._name = text
