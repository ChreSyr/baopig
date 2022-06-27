

from baopig._lib.hoverable import Hoverable
from .text import Text, DynamicText


def _init_loc(location):
    """ location: 'top', 'bottom', 'left' or 'right' """

    assert location in ("top", "bottom", "left", "right")
    if location == "top":
        loc_opposite = "bottom"
        pos = (0, -5)
    elif location == "bottom":
        loc_opposite = "top"
        pos = (0, 5)
    elif location == "left":
        loc_opposite = "right"
        pos = (-5, 0)
    elif location == "right":
        loc_opposite = "left"
        pos = (5, 0)
    else:
        raise ValueError(f"location must be 'top', 'bottom', 'left' or 'right'. Wrong value : {location}")

    return pos, loc_opposite


class Indicator(Text):

    def __init__(self, widget, text, indicator=None, location="top", **kwargs):
        """Create a Text above the widget when hovered"""

        assert isinstance(widget, Hoverable), "Indicator can only indicate Hoverable widgets"
        if widget._indicator is not None:
            raise PermissionError("A Widget can only have one indicator")
        if indicator is not None:
            widget._indicator = indicator
            raise NotImplementedError

        pos, loc_opposite = _init_loc(location)

        Text.__init__(
            self, widget.parent, text, font_color=(255, 255, 255), font_height=15,
            pos=pos, pos_location=loc_opposite, pos_ref=widget, pos_ref_location=location,
            background_color=(0, 0, 0, 192), padding=(8, 4), touchable=False, layer_level=2, **kwargs
        )

        widget._indicator = self
        self.origin.config(from_hitbox=True)
        widget.signal.HOVER.connect(self.wake, owner=self)
        widget.signal.UNHOVER.connect(self.sleep, owner=self)
        if not widget.is_hovered:
            self.sleep()


class DynamicIndicator(DynamicText):

    def __init__(self, widget, get_text, indicator=None, location="top", **kwargs):
        """Create a DynamicText above the widget when hovered"""

        if widget._indicator is not None:
            raise PermissionError("A Widget can only have one indicator")
        if indicator is not None:
            widget._indicator = indicator
            raise NotImplementedError

        pos, loc_opposite = _init_loc(location)

        DynamicText.__init__(
            self, widget.parent, get_text, font_color=(255, 255, 255), font_height=15,
            pos=pos, pos_location=loc_opposite, pos_ref=widget, pos_ref_location=location,
            background_color=(0, 0, 0, 192), padding=(8, 4), touchable=False, layer_level=2, **kwargs
        )

        widget._indicator = self
        self.origin.config(from_hitbox=True)
        widget.signal.HOVER.connect(self.wake, owner=self)
        widget.signal.UNHOVER.connect(self.sleep, owner=self)
        if not widget.is_hovered:
            self.sleep()
