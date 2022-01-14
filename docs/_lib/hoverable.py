

class Hoverable:
    """
    Abstract class for widgets who need to handle when they are hovered or unhovered
    A widget is hovered when the mouse is over it

    Example:

    class Obj(Widget, Hoverable)
        def __init__(self, blabla):
            Widget.__init__(self, blabla)
            Hoverable.__init__(self)
            self.signal.HOVER.add_command(lambda: print("Hovered"))
            self.signal.UNHOVER.add_command(lambda: print("Unhovered"))
    """

    def __init__(self):

        self._is_hovered = False
        self._indicator = None

        self.create_signal("HOVER")
        self.create_signal("UNHOVER")

        self.connect("handle_hover", self.signal.HOVER)
        self.connect("handle_unhover", self.signal.UNHOVER)

    indicator = property(lambda self: self._indicator)
    is_hovered = property(lambda self: self._is_hovered)

    def handle_hover(self):
        """Stuff to do when the widget gets hovered by mouse"""

    def handle_unhover(self):
        """Stuff to do when the widget is not hovered by mouse anymore"""

    def set_indicator(self, text=None, get_text=None, indicator=None):
        """
        Create a text above the widget when hovered

        :param text:
        :param get_text:
        :param indicator:
        """
        # NOTE : set_indicator function is added in baopig.widgets.Text

