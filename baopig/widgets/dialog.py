from baopig.lib import *
from .button import Button
from .text import Text


class DialogAnswerButton(Button):

    dialog = property(lambda self: self.scene)

    def handle_validate(self):

        self.dialog._answer(self.text_widget.text)


class DialogButtonsZone(Zone):
    STYLE = Zone.STYLE.substyle()
    STYLE.modify(
        pos=(0, -30),
        loc="midbottom",
        refloc="midbottom",
    )

    def __init__(self, dialog_frame):

        assert isinstance(dialog_frame, DialogFrame)

        choices = dialog_frame.parent.choices
        Zone.__init__(
            self, dialog_frame,
            size=(dialog_frame.rect.w - 60, int(46 * ((len(choices) - 1) / 3 + 1))),
        )
        grid = GridLayer(self, nbrows=int((len(choices) - 1) / 3) + 1, nbcols=min(len(choices), 3),
                         row_height=46, spacing=10)
        grid.set_col_width(int((self.rect.w - (grid.nbcols - 1) * grid.spacing.left) / grid.nbcols))
        for i, choice in enumerate(choices):
            assert isinstance(choice, str), "Other types are not implemented"
            self.dialog.style["answerbutton_class"](self, choice, col=i % 3, row=i // 3, loc="center")

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
        loc="center",
        width=450,
        height=300,
        background_color="theme-color-scene_background",
    )

    def __init__(self, dialog, **kwargs):
        assert isinstance(dialog, Dialog)

        Zone.__init__(self, dialog, **kwargs)

        self.buttons_zone = dialog.style["buttonszone_class"](self)

        self.title_label = Text(
            self, dialog.title,
            font_height=38,
            center=("50%", 40),
        )
        bottom = self.title_label.rect.bottom
        if dialog.description is not None:
            self.description_label = Text(
                self, dialog.description,
                font_height=27, max_width=self.rect.w - 60,
                pos=(30, self.title_label.rect.bottom + 15),
            )
            bottom = self.description_label.rect.bottom

        self.resize_height(max(bottom + 50 + self.buttons_zone.rect.height + 10, self.rect.height))


class Dialog(Scene):
    """
    Example :
        dialog = bp.Dialog(app, "Votre adversaire a quitté la partie en cours", choices=("OK",))
        def click_end_dialog(choice):
            app.open("menu")
        dialog.signal.ANSWERED.connect(click_end_dialog)

    If one_shot is True, this dialog will kill itself after the first answer
    """

    STYLE = Scene.STYLE.substyle()
    STYLE.create(
        title="Dialog",  # TODO : why are these style attributes ??
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

    def __init__(self, app, one_shot=False, **kwargs):

        Scene.__init__(self, app, **kwargs)

        self.title = self.style["title"]
        self.choices = self.style["choices"]
        self.description = self.style["description"]
        self.default_choice_index = self.style["default_choice_index"]
        assert self.default_choice_index in range(len(self.choices))
        self.frame = self.style["dialogframe_class"](self)  # TODO : a class style cannot be a parameter

        self.hovered_scene = None
        self.answer = None
        self.create_signal("ANSWERED")
        self.one_shot = one_shot

    def _answer(self, ans):
        """Only called by DialogAnswerButton"""
        self.answer = ans
        self.hovered_scene.open()
        self.signal.ANSWERED.emit(self.answer)
        if self.one_shot:
            self.kill()

    def handle_scene_open(self):
        self.focus(self.frame.buttons_zone.default_layer[self.default_choice_index])

    def open(self):

        if self.application.focused_scene is self:
            return

        app = self.application
        self.hovered_scene = app.focused_scene
        background_image = app.focused_scene.surface.copy()
        sail = pygame.Surface(app.size, pygame.SRCALPHA)
        sail.fill((0, 0, 0, 100))
        background_image.blit(sail, (0, 0))
        self.set_background_image(background_image)

        super().open()
