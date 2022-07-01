

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

        self.signal.HOVER.connect(self.handle_hover, owner=self)
        self.signal.UNHOVER.connect(self.handle_unhover, owner=self)

    indicator = property(lambda self: self._indicator)
    is_hovered = property(lambda self: self._is_hovered)

    def handle_hover(self):
        """Stuff to do when the widget gets hovered by mouse"""

    def handle_unhover(self):
        """Stuff to do when the widget is not hovered by mouse anymore"""