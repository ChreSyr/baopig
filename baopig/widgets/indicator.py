

from baopig.lib import HoverableByMouse
from .text import Text, DynamicText


def _init_loc(location):
    """ location: 'top', 'bottom', 'left' or 'right' """

    assert location in ("top", "bottom", "left", "right")
    if location == "top":
        loc_opposite = "midbottom"
        pos = (0, -5)
    elif location == "bottom":
        loc_opposite = "midtop"
        pos = (0, 5)
    elif location == "left":
        loc_opposite = "midright"
        pos = (-5, 0)
    elif location == "right":
        loc_opposite = "midleft"
        pos = (5, 0)
    else:
        raise ValueError(f"location must be 'top', 'bottom', 'left' or 'right'. Wrong value : {location}")

    return pos, loc_opposite


class Indicator(Text):

    def __init__(self, target, text, parent=None, indicator=None, loc="top", **kwargs):
        """Create a Text above the target when hovered"""

        assert isinstance(target, HoverableByMouse), "Indicator can only indicate HoverableByMouse widgets"
        if target._indicator is not None:
            raise PermissionError("A Widget can only have one indicator")
        if indicator is not None:
            target._indicator = indicator
            raise NotImplementedError

        pos, loc_opposite = _init_loc(loc)
        loc = "mid" + loc
        kwargs["loc"] = loc_opposite

        Text.__init__(
            self, target.parent if parent is None else parent, text, font_color=(255, 255, 255), font_height=15,
            pos=pos, ref=target, refloc=loc, referenced_by_hitbox=True,
            background_color=(0, 0, 0, 192), padding=(8, 4), selectable=False, layer_level=2, **kwargs
        )

        self.target = target
        target._indicator = self
        target.signal.HOVER.connect(self.handle_target_hover, owner=self)
        target.signal.UNHOVER.connect(self.handle_target_unhover, owner=self)
        if not target.is_hovered:
            self.handle_target_unhover()

    def handle_target_hover(self):
        self.wake()

    def handle_target_unhover(self):
        self.sleep()


class CasualIndicator(Indicator):

    def __init__(self, target, get_active, *args, **kwargs):

        self.get_active = get_active
        Indicator.__init__(self, target, *args, **kwargs)

    def handle_target_hover(self):
        if self.get_active():
            self.wake()
        else:
            self.sleep()

    def handle_target_unhover(self):
        self.sleep()


class DynamicIndicator(DynamicText):  # TODO : update like Indicator

    def __init__(self, widget, get_text, indicator=None, loc="top", **kwargs):
        """Create a DynamicText above the widget when hovered"""

        if widget._indicator is not None:
            raise PermissionError("A Widget can only have one indicator")
        if indicator is not None:
            widget._indicator = indicator
            raise NotImplementedError

        pos, loc_opposite = _init_loc(loc)
        loc = "mid" + loc
        kwargs["loc"] = loc_opposite

        DynamicText.__init__(
            self, widget.parent, get_text, font_color=(255, 255, 255), font_height=15, pos=pos,
            ref=widget, refloc=loc, referenced_by_hitbox=True,
            background_color=(0, 0, 0, 192), padding=(8, 4), selectable=False, layer_level=2, **kwargs
        )

        widget._indicator = self
        widget.signal.HOVER.connect(self.wake, owner=self)
        widget.signal.UNHOVER.connect(self.sleep, owner=self)
        if not widget.is_hovered:
            self.sleep()