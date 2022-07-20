from baopig.lib.style import Theme

"""

Color values from theme 'default' :

    border = (0, 0, 0)
    content = (0, 100, 125)
    font = (0, 0, 0)
    font_opposite = (255, 255, 255)
    scene_background = (170, 170, 170)
    selection = (167, 213, 255)
    selection_rect = (107, 107, 205)
    
"""


class DarkTheme(Theme):

    def __init__(self):
        super().__init__()
        self.colors.content = (168, 119, 30)
        self.colors.font = (220, 220, 220)
        self.colors.font_opposite = (0, 0, 0)
        self.colors.scene_background = (85, 85, 85)
        self.colors.selection = (24, 0, 200)
        self.colors.selection_rect = (0, 0, 0)


class GreenTheme(Theme):

    def __init__(self):
        super().__init__()
        self.colors.content = (0, 255, 0)
        self.colors.font_opposite = (100, 255, 100)
        self.colors.scene_background = (190, 210, 190)
        self.colors.selection = (0, 255, 0)
        self.colors.selection_rect = (0, 255, 0)

        from baopig.widgets.button import Button
        self.set_style_for(Button, width=400)


class PinkyTheme(Theme):

    def __init__(self):
        super().__init__()
        self.colors.border = (61, 12, 51)
        self.colors.content = (255, 117, 163)
        self.colors.scene_background = (255, 214, 220)
        self.colors.selection = (255, 53, 90)
        self.colors.selection_rect = (255, 53, 90)


all_themes = {
    "dark": DarkTheme(),
    "default": Theme(),
    "green": GreenTheme(),
    "pinky": PinkyTheme(),
}
