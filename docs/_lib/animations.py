
from .utilities import Closable
from baopig.time.timer import RepeatingTimer


class RepetivelyAnimated(Closable):
    """
    A RepetivelyAnimated object is a component who blinks every interval seconds

    WARNING : This class must be used with multiple heritance for components

    Exemple :

        class Lighthouse(Widget, RepetivelyAnimated):

    """

    def __init__(self, interval):
        """
        The component will appears and disappears every interval seconds

        :param interval: the time between appear and disappear
        """

        assert isinstance(interval, (int, float)), "interval must be a float or an integer"

        self.interval = interval

        def blink():
            if self.is_visible:
                self.hide()
            else:
                self.show()

        self.countdown_before_toggle_visibility = RepeatingTimer(interval, blink)

    def asleep(self):

        super().asleep()
        if self.countdown_before_toggle_visibility.is_paused:
            self.countdown_before_toggle_visibility.pause()

    def start_animation(self):

        if self.is_sleeping:
            self._memory.need_start_animation = True
            return

        if self.countdown_before_toggle_visibility.is_running:
            self.countdown_before_toggle_visibility.cancel()
        self.countdown_before_toggle_visibility.start()

    def stop_animation(self):

        if self.is_sleeping:
            self._memory.need_start_animation = False
            return

        self.countdown_before_toggle_visibility.cancel()

    def wake(self):

        super().wake()
        if self.countdown_before_toggle_visibility.is_paused:
            self.countdown_before_toggle_visibility.resume()
