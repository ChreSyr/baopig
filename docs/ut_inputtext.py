

from docs._lib import Scene
from docs.widgets.InputBox import InputBox


class UT_InputText_Scene(Scene):

    def __init__(self):

        Scene.__init__(self)

        InputBox(self, pos=(10, 10))
