

import pygame
from baopig._lib import Rectangle, Color
from .slider import Slider, SliderBar, SliderBloc
from .text import Text
from .numentry import NumEntry
from .dialog import Dialog, DialogFrame, DialogAnswerButton


class ColorSliderBloc(SliderBloc):

    # STYLE = SliderBloc.STYLE.substyle()
    # STYLE.modify(
    #     pos_location = "left",
    #     pos_ref_location = "left",
    # )

    def paint(self):

        self.surface.fill(self.border_color)
        pygame.draw.rect(
            self.surface, self.slider.color,
            (self.border_width, self.border_width, self.w - self.border_width * 2, self.h - self.border_width * 2)
        )


class ColorSliderBar(SliderBar):

    STYLE = SliderBar.STYLE.substyle()
    STYLE.modify(width = 260)

    slider = property(lambda self: self._parent)

    def paint(self):

        color = self.slider.color.copy()
        if self.border_color is not None:
            pygame.draw.rect(self.surface, self.border_color, (0, 0) + self.size, self.border_width * 2 - 1)
        bar_width = self.w-self.border_width*2
        for i in range(bar_width):
            if self.parent.attr in ("s", "v", "l"):
                color = self.slider.parent.color.copy()
            setattr(color, self.slider.attr, int(i / bar_width * (self.parent.maxval+1)))
            pygame.draw.line(
                self.surface, color,
                (i+self.border_width, self.border_width),
                (i+self.border_width, self.h-self.border_width*2)
            )


class ColorSlider(Slider):

    STYLE = Slider.STYLE.substyle()
    STYLE.modify(
        pos_location = "left",
        bloc_class = ColorSliderBloc,
        bar_class = ColorSliderBar,
    )

    def __init__(self, parent, attr, y, maxval=255, step=1, **kwargs):

        self.attr = attr
        self.color = parent.color.copy()
        self.color_before_link = None
        Slider.__init__(
            self, parent,
            minval=0, maxval=maxval, defaultval=getattr(parent.color, attr), step=step,
            pos=(parent.slider_x, y), **kwargs
        )
        parent.sliders.append(self)

        self.connect("handle_new_val", self.signal.NEW_VAL)

    def handle_link(self):

        # self.color = self.parent.color.copy()
        self.color_before_link = self.color.copy()
        super().handle_link()

    def handle_new_val(self, val):
        if self.is_linked:
            self.color = self.color_before_link.copy()
        setattr(self.color, self.attr, val)
        self.parent.update(self.color)

    def update(self):

        if self.is_linked: return self.bloc.paint()
        self.color = self.parent.color.copy()
        self._update_val(getattr(self.parent.color, self.attr))
        self.paint(recursive=True, only_containers=False)


class ColorEntry(NumEntry):

    STYLE = NumEntry.STYLE.substyle()
    STYLE.modify(
        pos_location = "left",
        width = 40,
    )

    def __init__(self, parent, attr, max, y):

        NumEntry.__init__(
            self, parent,
            min=0, max=max, accept_floats=False, default=getattr(parent.color, attr),
            pos=(parent.entry_x, y),
        )
        self.attr = attr
        self.parent.entries.append(self)

    def validate(self):

        setattr(self.parent.color, self.attr, int(self.text))
        self.lock_text(True)
        self.parent.update()
        self.lock_text(False)

    def update(self):

        val = str(int(getattr(self.parent.color, self.attr)))
        self.set_text(val)


class ColorAnswerButton(DialogAnswerButton):
    def validate(self):
        self.dialog._answer(self.dialog.frame.color)


class ColorDialogFrame(DialogFrame):

    STYLE = DialogFrame.STYLE.substyle()
    STYLE.modify(
        width = 600,
        height = 360,
    )

    def __init__(self, dialog, style=None):

        DialogFrame.__init__(self, dialog, style)
        self.color = Color(0, 0, 0)

        self.is_updating = False

        self.set_style_for(
            SliderBar,
            width=256 + 2,
        )

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
            pos=(0, -10), pos_location="bottom",
            pos_ref=self.color_rect, pos_ref_location="top"
        )

        if True:
            # RED
            self.red_label = Text(self, "Red :",
                pos=(self.label_x, self.red_y), pos_location="left")
            self.red_entry = ColorEntry(self, "r", 255, self.red_y)
            self.red_slider = ColorSlider(self, "r", self.red_y)

            # GREEN
            self.green_label = Text(self, "Green :",
                pos=(self.label_x, self.green_y), pos_location="left")
            self.green_entry = ColorEntry(self, "g", 255, self.green_y)
            self.green_slider = ColorSlider(self, "g", self.green_y)

            # BLUE
            self.blue_label = Text(self, "Blue :",
                pos=(self.label_x, self.blue_y), pos_location="left")
            self.blue_entry = ColorEntry(self, "b", 255, self.blue_y)
            self.blue_slider = ColorSlider(self, "b", self.blue_y)

        if True:
            # HUE
            self.hue_label = Text(self, "Hue :",
                pos=(self.label_x, self.hue_y), pos_location="left")
            self.hue_entry = ColorEntry(self, "h", 359, self.hue_y)
            self.hue_slider = ColorSlider(self, "h", self.hue_y, maxval=359)

            # SATURATION
            self.saturation_label = Text(self, "Saturation :",
                pos=(self.label_x, self.saturation_y), pos_location="left")
            self.saturation_entry = ColorEntry(self, "s", 100, self.saturation_y)
            self.saturation_slider = ColorSlider(self, "s", self.saturation_y, maxval=100)

            # SATURATION
            self.value_label = Text(self, "Value :",
                pos=(self.label_x, self.value_y), pos_location="left")
            self.value_entry = ColorEntry(self, "v", 100, self.value_y)
            self.value_slider = ColorSlider(self, "v", self.value_y, maxval=100)

            # SATURATION
            self.lightness_label = Text(self, "Lightness :",
                pos=(self.label_x, self.lightness_y), pos_location="left")
            self.lightness_entry = ColorEntry(self, "l", 100, self.lightness_y)
            self.lightness_slider = ColorSlider(self, "l", self.lightness_y, maxval=100)

    def update(self, color=None):

        if self.is_updating: return  # avoid update loops
        self.is_updating = True
        if color: self.color = color
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
        title = "Color Chooser",
        choices = ("Select",),
        dialogframe_class = ColorDialogFrame,
        answerbutton_class = ColorAnswerButton,
    )

