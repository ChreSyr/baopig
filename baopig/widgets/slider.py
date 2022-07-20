
from baopig.io import mouse
from baopig.lib import Rectangle, Container, LinkableByMouse
from .indicator import DynamicIndicator
from .text import Text


class SliderBloc(Rectangle):
    STYLE = Rectangle.STYLE.substyle()
    STYLE.modify(
        width=0,  # use length and wideness instead
        height=0,  # use length and wideness instead
        border_width=3,
    )
    STYLE.create(
        length=16,
        wideness="100%",
    )
    STYLE.set_constraint("height", lambda val: val == 0, "Use length and wideness instead of width and height")
    STYLE.set_constraint("width", lambda val: val == 0, "Use length and wideness instead of width and height")

    def __init__(self, slider):
        assert isinstance(slider, Slider)

        sticky = "midleft" if slider.axis == 'x' else "midtop"
        Rectangle.__init__(self, slider, sticky=sticky)

        assert self.rect.size == (0, 0), "Use length and wideness instead of size, width and height"

        self._length = self.style["length"]
        self._wideness = self.style["wideness"]
        self._max_x = None

        self.signal.RESIZE.connect(self.handle_resize, owner=None)

        if slider.axis == "x":
            self.resize(width=self._length, height=self._wideness)
        else:
            self.resize(width=self._wideness, height=self._length)

    slider = property(lambda self: self._parent)
    max_x = property(lambda self: self._max_x)

    def update(self):
        if self.slider.axis == "x":
            self.set_pos(left=self.slider.get_pourcent() * self.max_x)
        else:
            self.set_pos(top=self.slider.get_pourcent() * self.max_x)

    def handle_resize(self):

        if self.slider.axis == "x":
            self._max_x = self.slider.rect.width - self.rect.width
        else:
            self._max_x = self.slider.rect.height - self.rect.height


class SliderBar(Rectangle):
    STYLE = Rectangle.STYLE.substyle()
    STYLE.modify(
        loc="center",
        refloc="center",
        width=0,  # use length and wideness instead
        height=0,  # use length and wideness instead
        color=(0, 0, 0, 64),
        border_width=1,
    )
    STYLE.create(
        wideness="90%",  # length is defined by the slider
    )
    STYLE.set_constraint("height", lambda val: val == 0, "Use length and wideness instead of width and height")
    STYLE.set_constraint("width", lambda val: val == 0, "Use length and wideness instead of width and height")

    # NOTE : we replaced width/height with length/wideness, so it is easier to code vertical sliders

    def __init__(self, slider):
        assert isinstance(slider, Slider)

        # style = slider.get_style_for(self.__class__)
        # self.inherit_style_(slider)
        # TODO : if the slider goes vertically, switch length and wideness in the following line

        Rectangle.__init__(self, slider)

        assert self.rect.size == (0, 0), "Use length and wideness instead of size, width and height"

        self._length = 0  # self.style["length"]  TODO : remove length, defined by slider
        self._wideness = self.style["wideness"]
        if slider.axis == "x":
            self.resize(width=self._length, height=self._wideness)
        else:
            self.resize(width=self._wideness, height=self._length)


class Slider(Container, LinkableByMouse):
    """Widget that contains a bar and a slideable bloc"""

    STYLE = Container.STYLE.substyle()
    STYLE.modify(
        width=0,  # don't use them
        height=0,  # don't use them
    )
    # NOTE : On peut facilement se tromper en laissant width et height alors qu'on devrait utiliser bar_size
    STYLE.create(
        length=150,
        wideness=15,
        has_indicator=True,
        bloc_class=SliderBloc,
        bar_class=SliderBar,
        axis="x",
    )
    STYLE.set_type("has_indicator", bool)
    STYLE.set_constraint("axis", lambda val: val in ("x", "y"), "must be 'x' or 'y'")
    STYLE.set_constraint("bloc_class", lambda val: issubclass(val, SliderBloc))
    STYLE.set_constraint("bar_class", lambda val: issubclass(val, SliderBar))
    STYLE.set_constraint("height", lambda val: val == 0, "Use length and wideness instead of width and height")
    STYLE.set_constraint("width", lambda val: val == 0, "Use length and wideness instead of width and height")

    def __init__(self, parent, minval, maxval, defaultval=None, step=None, title=None, printed_title=False, **kwargs):

        if defaultval is None:
            defaultval = minval

        assert minval <= maxval, f"There must be a positive difference between minval and maxval " \
                                 f"(minval : {minval}, maxval : {maxval})"
        assert minval <= defaultval <= maxval, f"The defaultval must be included between minval and maxval " \
                                               f"(minval : {minval}, maxval : {maxval}, defaultval : {defaultval})"
        if step is not None:
            assert step > 0

        Container.__init__(self, parent, **kwargs)
        LinkableByMouse.__init__(self, parent)

        self._minval = minval
        self._maxval = maxval
        self._range = self.maxval - self.minval
        self._defaultval = self._val = defaultval
        self._step = step
        self._link_origin = None  # the link's position, relative to self
        self._axis = self.style["axis"]
        self._length = self.style["length"]
        self._wideness = self.style["wideness"]

        self.create_signal("NEW_VAL")

        self.bar = self.style["bar_class"](self)
        self.bloc = self.style["bloc_class"](self)

        assert self.rect.size == (0, 0), "Use length and wideness instead of size, width and height"
        if self.axis == "x":
            self.resize(width=self._length, height=self._wideness)
        else:
            self.resize(width=self._wideness, height=self._length)

        self.bloc.update()

        if self.style["has_indicator"]:
            if title:
                if printed_title:
                    self.title = Text(self, title, sticky="center", selectable=False, font_color=(96, 96, 96),
                                      font_height=int((self.bar.rect.height - self.bar.border_width * 2) * .9),
                                      font_bold=True)
                    self.title.set_touchable_by_mouse(False)
                DynamicIndicator(self, get_text=lambda: f"{title} : {self.val}")
            else:
                DynamicIndicator(self, get_text=lambda: self.val)

    axis = property(lambda self: self._axis)
    defaultval = property(lambda self: self._defaultval)
    maxval = property(lambda self: self._maxval)
    minval = property(lambda self: self._minval)
    range = property(lambda self: self._range)
    step = property(lambda self: self._step)
    val = property(lambda self: self._val)

    def _update_val(self, val=None, x=None):

        assert (val is None) != (x is None)

        if x is not None:
            current_x = self.bloc.rect.left if self.axis == "x" else self.bloc.rect.top
            if x == current_x:
                return
            # val = x * (max - min) / max_index + min
            val = x * self.range / self.bloc.max_x + self.minval
        if self.step is not None:
            def cut(n, length):
                # print(n, l, float(("{:." + str(l-1) + "e}").format(n)))
                return float(("{:." + str(length - 1) + "e}").format(n))

            val = round((val - self.minval) / self.step) * self.step + self.minval
            if isinstance(self.step, float):
                val = cut(val, len(str(self.step % 1)) - 2 + len(str(int(val))))
            if isinstance(val, float) and val.is_integer():  # remove .0 for the beauty of the indicator
                val = int(val)
            if val >= self.maxval:  # not else, because step can make val go to maxval or higher
                val = self.maxval

        if val == self.val:
            return
        assert self.minval <= val <= self.maxval, f"{val}, {self.maxval}, {self.minval}"

        self._val = val
        # x = (val - min) / (max - min) * max_index
        self.bloc.update()
        current_x = self.bloc.rect.left if self.axis == "x" else self.bloc.rect.top
        if current_x == 0:
            self._val = self.minval  # prevent approximations
        self.signal.NEW_VAL.emit(self.val)

    def get_pourcent(self):
        """Return the percentage from min to val in the range min -> max"""
        if self.range:
            return (self.val - self.minval) / self.range
        else:
            return 0

    def handle_link(self):

        def clamp(val, min_, max_):
            """Clamp f between min and max"""
            return min(max(val, min_), max_)

        size_index = 0 if self.axis == "x" else 1
        if self.bloc.collidemouse():
            self._link_origin = mouse.get_pos_relative_to(self.bloc)[size_index]
        else:
            size_val = self.bloc.rect.width if self.axis == "x" else self.bloc.rect.height
            self._link_origin = size_val / 2
            self._update_val(x=clamp(mouse.get_pos_relative_to(self)[size_index] - self._link_origin,
                                     0, self.bloc.max_x))

    def handle_link_motion(self, rel):

        def clamp(val, min_, max_):
            """Clamp f between min and max"""
            return min(max(val, min_), max_)

        size_index = 0 if self.axis == "x" else 1
        x = clamp(
            mouse.get_pos_relative_to(self)[size_index] - self._link_origin,
            0, self.bloc.max_x
        )
        self._update_val(x=x)

    def handle_resize(self):

        super().handle_resize()
        # TODO : bloc.length, bloc.wideness
        bar_margin = max(0, self.bloc.border_width - self.bar.border_width) * 2
        if self.axis == "x":
            self.bar.resize_width(self.rect.width - bar_margin)
        else:
            self.bar.resize_height(self.rect.height - bar_margin)

    def resize_TBR(self, w, h):
        pass
        # TODO : bloc.length, bloc.wideness

    def reset(self):
        """Set the value to defaultval"""
        if self.val == self.defaultval:
            return
        self._update_val(self.defaultval)

    def set_defaultval(self, val, reset=True):
        """If reset is True, reset the value to defaultval"""

        if val is self.defaultval:
            return
        assert self.minval <= val <= self.maxval, f"The value must be included between minval and maxval " \
                                                  f"(minval : {self.minval}, maxval : {self.maxval}, startval : {val})"

        self._defaultval = val
        if reset:
            self.reset()
