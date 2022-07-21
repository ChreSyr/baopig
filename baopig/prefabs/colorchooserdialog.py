import pygame
from baopig.lib import Rectangle, Color, paint_lock
from baopig.widgets.slider import Slider, SliderBar, SliderBloc
from baopig.widgets.text import Text
from baopig.widgets.numentry import NumEntry
from baopig.widgets.dialog import Dialog, DialogFrame, DialogAnswerButton


class ColorSliderBloc(SliderBloc):

    def paint(self):
        self.surface.fill(self.border_color)
        pygame.draw.rect(
            self.surface, self.slider.color,
            (self.border_width, self.border_width,
             self.rect.w - self.border_width * 2, self.rect.h - self.border_width * 2)
        )


class ColorSliderBar(SliderBar):

    slider = property(lambda self: self._parent)

    def paint(self):

        color = self.slider.color.copy()
        if self.border_color is not None:
            pygame.draw.rect(self.surface, self.border_color, (0, 0) + self.rect.size, self.border_width * 2 - 1)
        bar_width = self.rect.w - self.border_width * 2
        for i in range(bar_width):
            if self.parent.attr in ("s", "v", "l"):
                color = self.slider.parent.color.copy()
            setattr(color, self.slider.attr, int(i / bar_width * (self.parent.maxval + 1)))
            pygame.draw.line(
                self.surface, color,
                (i + self.border_width, self.border_width),
                (i + self.border_width, self.rect.h - self.border_width * 2)
            )


class ColorSlider(Slider):
    STYLE = Slider.STYLE.substyle()
    STYLE.modify(
        length=260,
        loc="midleft",
        bloc_class=ColorSliderBloc,
        bar_class=ColorSliderBar,
    )

    def __init__(self, parent, attr, y, maxval=255, **kwargs):

        self.attr = attr
        self.color = parent.color.copy()
        self.color_before_link = None
        Slider.__init__(
            self, parent,
            minval=0, maxval=maxval, defaultval=getattr(parent.color, attr), step=1,
            pos=(parent.slider_x, y), **kwargs
        )
        parent.sliders.append(self)

        self.signal.NEW_VAL.connect(self.handle_new_val, owner=self)

    def handle_link(self):

        self.color_before_link = self.color.copy()
        super().handle_link()

    def handle_new_val(self, val):
        if self.is_linked:
            self.color = self.color_before_link.copy()
        setattr(self.color, self.attr, val)
        self.parent.update(self.color)

    def handle_unlink(self):

        self.update()

    def update(self):

        if self.is_linked:
            return self.bloc.send_paint_request()
        self.color = self.parent.color.copy()
        self._update_val(getattr(self.parent.color, self.attr))
        with paint_lock:
            self.bloc.send_paint_request()
            self.bar.send_paint_request()


class ColorEntry(NumEntry):
    STYLE = NumEntry.STYLE.substyle()
    STYLE.modify(
        loc="midleft",
        padding=2,
    )

    def __init__(self, parent, attr, maxval, y):
        NumEntry.__init__(
            self, parent,
            minval=0, maxval=maxval, accept_floats=False, default=getattr(parent.color, attr),
            pos=(parent.entry_x, y),
        )
        self.attr = attr
        self.parent.entries.append(self)

    def handle_validate(self):
        super().handle_validate()
        setattr(self.parent.color, self.attr, int(self.text))
        self.parent.update()

    def update(self):
        val = str(round(getattr(self.parent.color, self.attr)))
        self.set_text(val)


class ColorAnswerButton(DialogAnswerButton):
    def handle_validate(self):
        self.dialog._answer(self.dialog.frame.color)


class ColorDialogFrame(DialogFrame):
    STYLE = DialogFrame.STYLE.substyle()
    STYLE.modify(
        width=600,
        height=360,
    )

    def __init__(self, dialog, **kwargs):

        DialogFrame.__init__(self, dialog, **kwargs)
        self.color = Color(0, 0, 0)

        self.is_updating = False

        self.set_style_for(ColorSlider, length=256 + 2, wideness=13)

        self.label_x = 10
        self.entry_x = self.label_x + 5 + 90
        self.slider_x = self.entry_x + 5 + 45

        self.red_y = 100
        self.green_y = self.red_y + 20 + 5
        self.blue_y = self.green_y + 20 + 5
        self.rgb_y = [self.red_y, self.green_y, self.blue_y]
        self.hue_y = self.blue_y + 20 + 5
        self.saturation_y = self.hue_y + 20 + 5
        self.value_y = self.saturation_y + 20 + 5
        self.lightness_y = self.value_y + 20 + 5

        self.sliders = []
        self.entries = []

        pos = (self.slider_x + 300, self.red_y - 20)
        self.color_rect = Rectangle(
            self, color=self.color,
            size=(100, self.lightness_y + 20 - pos[1]),
            pos=pos
        )
        self.color_text = Text(
            self, str(self.color),
            midbottom=(0, -10),
            ref=self.color_rect, refloc="midtop"
        )

        if True:
            # RED
            self.red_label = Text(self, "Red :", midleft=(self.label_x, self.red_y))
            self.red_entry = ColorEntry(self, "r", 255, self.red_y)
            self.red_slider = ColorSlider(self, "r", self.red_y)

            # GREEN
            self.green_label = Text(self, "Green :", midleft=(self.label_x, self.green_y))
            self.green_entry = ColorEntry(self, "g", 255, self.green_y)
            self.green_slider = ColorSlider(self, "g", self.green_y)

            # BLUE
            self.blue_label = Text(self, "Blue :", midleft=(self.label_x, self.blue_y))
            self.blue_entry = ColorEntry(self, "b", 255, self.blue_y)
            self.blue_slider = ColorSlider(self, "b", self.blue_y)

        if True:
            # HUE
            self.hue_label = Text(self, "Hue :", midleft=(self.label_x, self.hue_y))
            self.hue_entry = ColorEntry(self, "h", 359, self.hue_y)
            self.hue_slider = ColorSlider(self, "h", self.hue_y, maxval=359)

            # SATURATION
            self.saturation_label = Text(self, "Saturation :", midleft=(self.label_x, self.saturation_y))
            self.saturation_entry = ColorEntry(self, "s", 100, self.saturation_y)
            self.saturation_slider = ColorSlider(self, "s", self.saturation_y, maxval=100)

            # SATURATION
            self.value_label = Text(self, "Value :", midleft=(self.label_x, self.value_y))
            self.value_entry = ColorEntry(self, "v", 100, self.value_y)
            self.value_slider = ColorSlider(self, "v", self.value_y, maxval=100)

            # SATURATION
            self.lightness_label = Text(self, "Lightness :", midleft=(self.label_x, self.lightness_y))
            self.lightness_entry = ColorEntry(self, "l", 100, self.lightness_y)
            self.lightness_slider = ColorSlider(self, "l", self.lightness_y, maxval=100)

    def update(self, color=None):

        if self.is_updating:
            return  # avoid update loops
        self.is_updating = True
        if color:
            self.color = color
        for entry in self.entries:
            entry.update()
        for slider in self.sliders:
            slider.update()
        self.color_rect.set_color(self.color)
        self.color_text.set_text(str(self.color))
        self.is_updating = False


class ColorChooserDialog(Dialog):
    STYLE = Dialog.STYLE.substyle()
    STYLE.modify(
        title="Color Chooser",
        choices=("Select",),
        dialogframe_class=ColorDialogFrame,
        answerbutton_class=ColorAnswerButton,
    )
