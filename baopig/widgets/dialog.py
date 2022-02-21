import time
from baopig._lib import *
from .text import Text
from .button import Button


class DialogAnswerButton(Button):

    def get_dialog(self):
        dialog = self.parent
        while not isinstance(dialog, Dialog):
            if isinstance(dialog, Scene):
                raise TypeError("A DialogAnswerButton must be inside a Dialog")
            dialog = dialog.parent
        return dialog

    dialog = property(get_dialog)

    def validate(self):

        self.dialog._answer(self.text_widget.text)


class DialogButtonsZone(Zone):
    STYLE = Zone.STYLE.substyle()
    STYLE.modify(
        pos=(0, -30),
        pos_location="bottom",
        pos_ref_location="bottom",
        background_color=(0, 0, 0, 60),
    )

    def __init__(self, dialog_frame):

        assert isinstance(dialog_frame, DialogFrame)

        choices = dialog_frame.parent.choices
        Zone.__init__(
            self, dialog_frame,
            size=(dialog_frame.w - 60, 46 * ((len(choices) - 1) / 3 + 1)),
        )
        GridLayer(self, nbrows=int((len(choices) - 1) / 3) + 1, nbcols=min(len(choices), 3),
                  row_height=46, col_width=int(self.w / min(len(choices), 3)))
        for i, choice in enumerate(choices):
            assert isinstance(choice, str), "Other types are not implemented"
            self.dialog.style["answerbutton_class"](self, choice, col=i % 3, row=i // 3, sticky="center")

    def get_dialog(self):
        dialog = self.parent
        while not isinstance(dialog, Dialog):
            if isinstance(dialog, Scene):
                raise TypeError("A DialogAnswerButton must be inside a Dialog")
            dialog = dialog.parent
        return dialog

    dialog = property(get_dialog)


class DialogFrame(Zone):
    STYLE = Zone.STYLE.substyle()
    STYLE.modify(
        pos=("50%", "50%"),
        pos_location="center",
        width=450,
        height=300,
        background_color="theme-color-dialog_background",
    )

    def __init__(self, dialog, style):
        assert isinstance(dialog, Dialog)

        self.inherit_style(dialog, style)
        Zone.__init__(self, dialog)

        self.buttons_zone = dialog.style["buttonszone_class"](self)

        self.title_label = Text(
            self, dialog.title,
            font_height=38,
            pos=("50%", 40), pos_location="center"
        )
        bottom = self.title_label.bottom
        if dialog.description is not None:
            self.description_label = Text(
                self, dialog.description,
                font_height=27, max_width=self.w - 60,
                pos=(30, self.title_label.bottom + 15),
            )
            bottom = self.description_label.bottom

        self.resize_height(max(bottom + 50 + self.buttons_zone.height + 10, self.height))


class Dialog(Scene):
    """
    If one_shot is True, this dialog widget will kill itself after the first answer
    """

    STYLE = Scene.STYLE.substyle()
    STYLE.create(
        title="Dialog",
        description=None,
        choices=("Cancel", "Continue"),
        default_choice_index=0,  # focuses the first answer button
        dialogframe_class=DialogFrame,
        buttonszone_class=DialogButtonsZone,
        answerbutton_class=DialogAnswerButton,
    )
    STYLE.set_type("title", str)
    STYLE.set_type("default_choice_index", int)
    STYLE.set_constraint("dialogframe_class", lambda val: issubclass(val, DialogFrame),
                         "must be a subclass of DialogFrame")
    STYLE.set_constraint("buttonszone_class", lambda val: issubclass(val, DialogButtonsZone),
                         "must be a subclass of DialogButtonsZone")
    STYLE.set_constraint("answerbutton_class", lambda val: issubclass(val, DialogAnswerButton),
                         "must be a subclass of DialogAnswerButton")

    def __init__(self, app, title=None, choices=None, description=None, default_choice_index=0,
                 frame_style=None, one_shot=False, background_image=None):

        self.inherit_style(
            app,
            title=title, choices=choices, description=description,
            default_choice_index=default_choice_index,
        )

        Scene.__init__(self, app)

        self.title = self.style["title"]
        self.choices = self.style["choices"]
        self.description = self.style["description"]
        self.default_choice_index = self.style["default_choice_index"]
        assert self.default_choice_index in range(len(self.choices))
        if background_image:
            self.set_style_for(
                self.style["dialogframe_class"],
                background_image=background_image,
            )
        self.frame = self.style["dialogframe_class"](self, frame_style)

        self.answer = None
        self.create_signal("ANSWERED")
        self.one_shot = one_shot

    def pre_open(self):

        app = self.application
        self.hovered_scene = app.focused_scene
        background = app.display.copy()
        sail = pygame.Surface(app.size, pygame.SRCALPHA)
        sail.fill((0, 0, 0, 100))
        background.blit(sail, (0, 0))
        self.set_background_image(background)

    def open(self):
        self._focus(self.frame.buttons_zone.default_layer[self.default_choice_index])

    def _answer(self, ans):
        """Only called by DialogAnswerButton"""
        self.answer = ans
        self.app.open(self.hovered_scene)  # TODO : self.hovered_scene.open()
        self.signal.ANSWERED.emit(self.answer)
        if self.one_shot:
            self.kill()
