import time
from baopig.documentation import ScrollableByMouse as ScrollableByMouseDoc
from baopig.io import keyboard
from baopig.lib import Rectangle
from baopig.lib import Zone, LayersManager
from .slider import Slider, SliderBar, SliderBloc


class ScrollBloc(SliderBloc):
    STYLE = SliderBloc.STYLE.substyle()
    STYLE.modify(
        wideness=10,
        border_width=0,
        color=(100, 100, 100, 63)
    )

    def __init__(self, slider):

        SliderBloc.__init__(self, slider)

        slider.signal.NEW_VAL.connect(self.update_length, owner=self)

    def update_length(self):

        try:
            if self.slider.axis == "x":
                self.resize_width(int(self.slider.rect.width ** 2 / self.slider.parent.main_widget.rect.width))
            else:
                self.resize_height(int(self.slider.rect.height ** 2 / self.slider.parent.main_widget.rect.height))
        except ZeroDivisionError:  # main_widget's length is null
            pass


class ScrollBar(SliderBar):
    STYLE = SliderBar.STYLE.substyle()
    STYLE.modify(
        wideness=10,
        border_width=0,
        color=(0, 0, 0, 0)
    )


class ScrollSlider(Slider):
    STYLE = Slider.STYLE.substyle()
    STYLE.modify(
        bloc_class=ScrollBloc,
        bar_class=ScrollBar,
        has_indicator=False,
        wideness=10,
    )

    def __init__(self, scroller, axis):

        assert isinstance(scroller, ScrollView)

        self._parent = scroller
        self._axis = axis

        if axis == "x":
            pos = (0, 0)
            sticky = "midbottom"
            length = scroller.content_rect.width
        else:
            pos = (0, 0)
            sticky = "midright"
            length = scroller.content_rect.height

        Slider.__init__(
            self, scroller, step=1e-9, axis=axis, pos=pos, sticky=sticky, layer_level=LayersManager.FOREGROUND,
            minval=0, maxval=scroller.max[axis], length=length,
        )

        self.signal.NEW_VAL.connect(self.handle_new_val, owner=None)

        self._hover_sail_ref = Rectangle(self, size=("100%", "100%"), touchable=False, color=(255, 255, 255, 63),
                                         visible=False).get_weakref()

        if not self.range:
            self.hide()

    hover_sail = property(lambda self: self._hover_sail_ref())

    def handle_hover(self):

        self.hover_sail.show()

    def handle_unhover(self):

        self.hover_sail.hide()

    def handle_new_val(self):

        self.parent._set_scrollval(self.axis, self.val)

    def set_val(self, val):

        self._update_val(val=val)

    def update_from_mainwidget_resize(self):

        maxval = self.parent.max[self.axis]

        if maxval == self.maxval:
            return

        self._range = self._maxval = maxval

        if self.axis == "x":
            val = - self.parent.main_widget.rect.left
        else:
            val = - self.parent.main_widget.rect.top

        if val == self.val:
            self.bloc.update()
            self.handle_new_val()
        else:
            self.set_val(val)
        self.bloc.update_length()

        if maxval:
            self.show()
        else:
            self.hide()


class ScrollView(ScrollableByMouseDoc, Zone):
    STYLE = Zone.STYLE.substyle()
    STYLE.create(
        scrollslider_class=ScrollSlider
    )

    def __init__(self, parent, **kwargs):

        Zone.__init__(self, parent, **kwargs)

        # TODO : add padding, so blank space for easy cursor control
        assert self.padding.is_null, "ScrollView does not support padding"

        self.max = {"x": 0, "y": 0}
        self._last_scroll_time = 0

        scrollslider_class = self.style["scrollslider_class"]
        self._x_scroller_ref = scrollslider_class(self, axis="x").get_weakref()
        self._y_scroller_ref = scrollslider_class(self, axis="y").get_weakref()

        self._main_widget = None

    main_widget = property(lambda self: self._main_widget())
    x_scroller = property(lambda self: self._x_scroller_ref())
    y_scroller = property(lambda self: self._y_scroller_ref())

    def _add_child(self, child):

        super()._add_child(child)
        if child.layer.level == LayersManager.MAINGROUND:
            assert self._main_widget is None, "A ScrollView cannot contain more than one widget"
            self._main_widget = child.get_weakref()
            self._handle_mainwidget_resize()
            self.main_widget.signal.RESIZE.connect(self._handle_mainwidget_resize, owner=None)

    def _handle_mainwidget_resize(self):

        self.max = {
            "x": max(0, self.main_widget.rect.width - self.rect.width),
            "y": max(0, self.main_widget.rect.height - self.rect.height),
        }

        rect = self.main_widget.rect
        dx = 0
        if 0 <= (self.rect.width - rect.right) <= - rect.left:
            dx = (self.rect.width - rect.right)
        dy = 0
        if 0 <= (self.rect.height - rect.bottom) <= - rect.top:
            dy = (self.rect.height - rect.bottom)
        if dx or dy:
            self.main_widget.move(dx, dy)

        self.x_scroller.update_from_mainwidget_resize()
        self.y_scroller.update_from_mainwidget_resize()

    def _set_scrollval(self, axis, val):

        if axis == "x":
            self.main_widget.set_pos(left=-val)
        else:
            self.main_widget.set_pos(top=-val)

    def handle_mouse_scroll(self, scroll_event):

        old_scroll_time = self._last_scroll_time
        self._last_scroll_time = time.time()
        d = self._last_scroll_time - old_scroll_time

        accelerator = 10
        if d < .1:
            accelerator = 1 / d

        if keyboard.mod.maj:
            scroller = self.x_scroller
        else:
            scroller = self.y_scroller

        if scroll_event.button == 4:
            direction = -1
        else:
            direction = 1

        val = scroller.val + accelerator * direction
        val = min(max(0, val), scroller.maxval)

        scroller.set_val(val)

    def handle_resize(self):

        super().handle_resize()
        self.x_scroller.resize_width(self.rect.w)  # TODO
        self.y_scroller.resize_height(self.rect.h)
