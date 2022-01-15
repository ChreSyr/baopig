

import pygame
from baopig._lib import *
from .text import Text, DynamicText


class SliderBloc(Rectangle):

    STYLE = Rectangle.STYLE.substyle()
    STYLE.modify(
        width = -1,   # use length and wideness instead
        height = -1,  # use length and wideness instead
        border_width = 3,
        pos_location = "left",
        pos_ref_location = "left",
    )
    STYLE.create(
        length = 16,
        wideness = 14,
    )

    def __init__(self, slider):

        assert isinstance(slider, Slider)

        self._border_width = 0
        self.inherit_style(slider)  # anticipated inheritance
        self._border_width = self.style["border_width"]
        # TODO : if the slider goes vertically, switch length and wideness in the following line
        self.style.modify(width=self.style["length"], height=self.style["wideness"])

        Rectangle.__init__(self, slider)

        self._max_index = None  # TODO : remove

    slider = property(lambda self: self._parent)
    x_max = property(lambda self: self._max_index)

    def update(self):

        self.x = self.slider.get_pourcent() * self.x_max


class SliderBar(Rectangle):

    STYLE = Rectangle.STYLE.substyle()
    STYLE.modify(
        pos_location = "center",
        pos_ref_location = "center",
        width = -1,  # TODO : delete, but is it possible ? maybe not
        height = -1,  # TODO : delete
        color = (0, 0, 0, 64),
        border_width = 1,
    )
    STYLE.create(
        length = 150,
        wideness = 10,
    )
    # NOTE : we replaced width/height with length/wideness, so it is easier to code vertical sliders

    def __init__(self, slider):

        assert isinstance(slider, Slider)

        style = slider.get_style_for(self.__class__)
        self.inherit_style(slider)
        # TODO : if the slider goes vertically, switch length and wideness in the following line
        self.style.modify(width=style["length"], height=style["wideness"])

        Rectangle.__init__(self, slider)


class Slider(Container, Linkable, Hoverable):
    """Widget that contains a bar and a slideable bloc"""

    STYLE = Container.STYLE.substyle()
    STYLE.modify(
        width = -1,   # don't use them
        height = -1,  # don't use them
    )
    # NOTE : On peut facilement se tromper en laissant width et height alors qu'on devrait utiliser bar_size
    STYLE.create(
        has_indicator = True,
        bloc_class = SliderBloc,
        bar_class = SliderBar,
        axis = "x",
    )
    STYLE.set_constraint("axis", lambda val: val in ("x", "y"), "must be 'x' or 'y'")

    STYLE.set_type("has_indicator", bool)
    STYLE.set_constraint("bloc_class", lambda val: issubclass(val, SliderBloc))
    STYLE.set_constraint("bar_class", lambda val: issubclass(val, SliderBar))

    def __init__(self, parent, minval, maxval,
                 bloc_class=None, bar_class=None, has_indicator=None, bar_size=None,
                 defaultval=None, step=None, title=None, printed_title=False, **options):

        if "size" in options:
            raise PermissionError("Use bar_size instead of size")

        self.inherit_style(parent, options)

        if defaultval is None: defaultval = minval

        assert minval < maxval, f"There must be a positive difference between minval and maxval " \
                                f"(minval : {minval}, maxval : {maxval})"
        assert minval <= defaultval <= maxval, f"The defaultval must be included between minval and maxval " \
                                             f"(minval : {minval}, maxval : {maxval}, defaultval : {defaultval})"
        if step is not None: assert step > 0

        if bar_size is not None:  # TODO : bar_style
            self.set_style_for(self.style["bar_class"], width=bar_size[0], height=bar_size[1])

        bar_style = self.get_style_for(self.style["bar_class"])
        # TODO : if the slider goes vertically, switch length and wideness in the following line
        self.style.modify(width=bar_style["length"], height=bar_style["wideness"])
        Container.__init__(self, parent, **options)
        Linkable.__init__(self)
        Hoverable.__init__(self)

        self._minval = minval
        self._maxval = maxval
        self._range = self.maxval - self.minval
        self._defaultval = self._val = defaultval
        self._step = step
        self._link_origin = None  # the link x position, relative to self
        self._axis = self.style["axis"]

        self.bar = self.style["bar_class"](self)
        self.bloc = self.style["bloc_class"](self)

        self.resize(
            self.bar.width + max(0, self.bloc.border_width - self.bar.border_width) * 2,
            max(self.bar.height, self.bloc.height),
        )
        self._max_bloc_index = self.bloc._max_index = self.width - self.bloc.width
        self.bloc.update()

        self.create_signal("NEW_VAL")

        if self.style["has_indicator"]:
            get_indicator_text = lambda: self.val
            if title:
                if printed_title:
                    self.title = Text(
                        self, title,
                        color=(96, 96, 96), font_height=int((self.bar.height - self.bar.border_width*2) * .9), bold=True,
                        sticky="center", touchable=False
                    )
                get_indicator_text = lambda: title + f" : {self.val}"
            self.set_indicator(get_text=get_indicator_text)

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
            if x == self.bloc.x: return
            # val = x * (max - min) / max_index + min
            val = x * self.range / self._max_bloc_index + self.minval
        if self.step is not None:
            def cut(n, l):
                # print(n, l, float(("{:." + str(l-1) + "e}").format(n)))
                return float(("{:." + str(l-1) + "e}").format(n))
            val = round((val - self.minval) / self.step) * self.step + self.minval
            if isinstance(self.step, float):
                val = cut(val, len(str(self.step % 1)) - 2 + len(str(int(val))))
            if isinstance(val, float) and val.is_integer():  # remove .0 for the beauty of the indicator
                val = int(val)
            if val >= self.maxval:  # not else, because step can make val go to maxval or higher
                val = self.maxval

        if val == self.val: return
        assert self.minval <= val <= self.maxval, f"{val}, {self.maxval}, {self.minval}"

        self._val = val
        # x = (val - min) / (max - min) * max_index
        self.bloc.update()
        if self.bloc.x == 0: self._val = self.minval  # prevent approximations
        self.signal.NEW_VAL.emit(self.val)

    def get_pourcent(self):
        """Return the percentage from min to val in the range min -> max"""
        return (self.val - self.minval) / self.range

    def handle_link(self):

        def clamp(val, min_, max_):
            """Clamp f between min and max"""
            return min(max(val, min_), max_)

        if self.bloc.collidemouse():
            self._link_origin = mouse.get_pos_relative_to(self.bloc)[0]
        else:
            self._link_origin = self.bloc.width / 2
            self._update_val(x=clamp(mouse.get_pos_relative_to(self)[0] - self._link_origin,
                                     0, self._max_bloc_index))

    def handle_link_motion(self, link_motion_event):

        def clamp(val, min_, max_):
            """Clamp f between min and max"""
            return min(max(val, min_), max_)

        x = clamp(
            mouse.get_pos_relative_to(self)[0] - self._link_origin,
            0, self._max_bloc_index
        )
        self._update_val(x=x)

    def resize(self, w, h):

        super().resize(w, h)

        bar_margin = max(0, self.bloc.border_width - self.bar.border_width) * 2
        self.bar.resize_width(self.width - bar_margin)

        # TODO : bloc.length, bloc.wideness

    def reset(self):
        """Set the value to defaultval"""
        if self.val == self.defaultval: return
        self._update_val(self.defaultval)

    def set_defaultval(self, val, reset=True):
        """If reset is True, reset the value to defaultval"""

        if val is self.defaultval: return
        assert self.minval <= val <= self.maxval, f"The value must be included between minval and maxval " \
                                f"(minval : {self.minval}, maxval : {self.maxval}, startval : {val})"

        self._defaultval = val
        if reset: self.reset()

