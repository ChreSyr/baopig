from baopig._lib import Scrollable, ScrollableByMouse, Size, MarginType
from baopig._lib import Zone, Rectangle, LayersManager
from .slider import Slider, SliderBar, SliderBloc


class ScrollSlider(Slider):
    STYLE = Slider.STYLE.substyle()
    STYLE.modify(
        width=10,
        height=0,
    )

    def __init__(self, scroller, axis, style):

        assert isinstance(scroller, Scrollable)

        self.inherit_style(scroller, style)
        assert self.style["height"] == 0, \
            "You cannot define height on a ScrollSlider, it is automatically generated"

        border = MarginType(self.theme[SliderBar]["border_width"])
        scroller_size = scroller.window[2:]
        width = self.style["width"]
        self._parent = scroller  # needed in get_length()
        self._axis = axis  # needed in get_length()
        length = self.get_length()
        if axis == "x":
            bloc_style = {"width": length, "height": width}
            pos = (0, border.bottom)
            sticky = "bottom"
            size = (scroller_size[0] + border.left + border.right, width)
        else:
            bloc_style = {"width": width, "height": length}
            pos = (border.right, 0)
            sticky = "right"
            size = (width, scroller_size[1] + border.top + border.bottom)
        bloc_style["border_width"] = 0
        self.set_style_for(SliderBloc, **bloc_style)

        Slider.__init__(
            self, scroller, 0, 100, step=1e-9, axis=axis,
            pos=pos, sticky=sticky, bar_size=size, pos_from_ref_hitbox=True,
            layer_level=LayersManager.FOREGROUND
        )

    def get_length(self):

        if self.axis == "y":
            return self.parent.hitbox.height / self.parent.height * self.parent.window[3]
        else:
            return self.parent.hitbox.width / self.parent.width * self.parent.window[2]


class ScrollableZone(Zone, ScrollableByMouse):
    STYLE = Zone.STYLE.substyle()
    STYLE.create(
        scrollslider_class=ScrollSlider
    )
    STYLE.set_constraint("scrollslider_class", lambda val: issubclass(val, ScrollSlider))

    def __init__(self, parent, window_size, bar_style=None, **options):

        Zone.__init__(self, parent, **options)

        self._scrollaxis = ""
        self.scrollsliders = []
        scrollslider_class = self.style["scrollslider_class"]

        self.set_window(self.pos + Size(window_size))
        assert self.rect.contains(self.rect.__class__(self.window))  # TODO : remove
        if self.width > window_size[0]:
            self._scrollaxis += "x"
            self.scrollsliders.append(scrollslider_class(self, "x", bar_style))
        if self.height > window_size[1]:
            self._scrollaxis += "y"
            self.scrollsliders.append(scrollslider_class(self, "y", bar_style))
        ScrollableByMouse.__init__(self, self.scrollaxis)

    def get_scroll_pourcent(self, axis):

        assert axis in "x", "y"

        if axis == "x":
            return self.window[0] / (self.width - self.window[2])
        else:
            return self.window[1] / (self.height - self.window[3])
