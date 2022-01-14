
import time
import threading
import math
from pyapp.logging import LOGGER


class Countdown:
    """
    A Countdown is like a timer :
        Yous set start()
        interval seconds later, it execute the function

    To start the countdown:  start()
    To read the countdown:   get_time()
    To cancel the countdown: cancel()
    """

    MILLISECONDS = 0
    SECONDS = 1
    MINUTES = 2
    HOURS = 3

    def __init__(self, interval, function=None):

        if function is None: function = lambda: None

        assert isinstance(interval, (int, float)), "interval must be a float or an integer"
        assert callable(function), "function must be callable"

        self._timer = None  # a threading.Timer
        self._interval = interval
        self._handle_timeout = function
        self._start_time = None

    interval = property(lambda self: self._interval)
    is_running = property(lambda self: self._start_time is not None)

    def __str__(self):
        return self.get_string_time()

    def __repr__(self):
        return "<Countdown(time_left:{}, timer:{})>".format(self.get_string_time(precision=0), self._timer)

    def cancel(self):

        if not self.is_running:  # The countdown is not running, don't need to be canceled
            return

        self._timer.cancel()
        anc_timer = self._timer
        del anc_timer
        self._timer = None
        self._start_time = None

        # LOGGER.debug("Canceled countdown")

    def get_string_time(self, precision=0):
        """
        Return the timer time in a string format
        precision must be one of HOURS, MINUTES, SECONDS, MILLISECONDS

        :param precision: a number
        :return: a string time
        """
        assert precision in (Countdown.HOURS, Countdown.MINUTES, Countdown.SECONDS, Countdown.MILLISECONDS), "" \
            "precision must be one of Countdown.HOURS, Countdown.MINUTES, Countdown.SECONDS, Countdown.MILLISECONDS"

        def sec_to_date(seconds, format=1):
            """

            Creation d'un string qui presente l'heure en fonction du temps t
            Le format est l'unite
            134, 1 -> 02:14 (m:s)

            MILLISECONDS = 0
            SECONDS = 1
            MINUTES = 2
            HOURS = 3

            :param seconds: un temps en secondes
            :param format: un nombre qui indique le format
            :return: un string representant l'heure
            """
            date = ""

            # Hours
            if format == 3 and seconds % 3600 != 0:
                seconds += 3600  # When there is 3.4 hours left, I want to see 4 hours
            hours = str(int(seconds // 3600))
            while len(hours) < 2:
                hours = "0" + hours
            date += hours
            if format == 3:
                return date
            seconds = seconds % 3600

            # Minutes
            if format == 2 and seconds % 60 > 0:
                seconds += 60  # When there is is 3.4 minutes left, I want to see 4 minutes
            minutes = str(int(seconds // 60))
            while len(minutes) < 2:
                minutes = "0" + minutes
            date += ":" + minutes
            if format == 2:
                return date
            seconds = seconds % 60

            # Seconds
            milliseconds = str(int(seconds % .001 * 1000000))
            if format == 1 and int(milliseconds) != 0:
                seconds += 1  # When there is is 3.4 seconds left, I want to see 4 seconds
            seconds = str(int(seconds))
            while len(seconds) < 2:
                seconds = "0" + seconds
            date += ":" + seconds
            if format == 1:
                return date

            # Milliseconds
            while len(milliseconds) < 3:
                milliseconds = "0" + milliseconds
            date += ":" + milliseconds
            if format == 0:
                return date

            # Wrong format
            return date

        return sec_to_date(self.get_time_left(), precision)

    def get_time_left(self):
        """
        Return the number of seconds before the countdown is over
        """
        if not self.is_running:
            return 0

        return self._start_time + self._interval - time.time()

    def handle_timeout(self):
        """
        Method qui termine le countdown
        et execute self.request
        Sera automatiquement appelee a la fin du thread
        :return: None
        """
        if not self.is_running:
            LOGGER.exception("handle_timeout called but countdown is not initialized")
            return

        anc_timer = self._timer
        del anc_timer
        self._timer = None
        self._start_time = None
        self._handle_timeout()

        # LOGGER.debug("Countdown is over")

    def set_interval(self, interval):

        self._interval = interval

    def start(self):

        if self.is_running:
            self.cancel()

        self._start_time = time.time()  # in seconds
        self._timer = threading.Timer(self._interval, self.handle_timeout)
        self._timer.start()
    restart = start


class RepeatingCountdown(Countdown):
    """
    A RepeatingCountdown is like a repeating timer :
        Yous set start()
        At every interval seconds later, it execute the function

    To start the countdown:  start()
    To read the countdown:   get_time()
    To cancel the countdown: cancel()
    """
    def __init__(self, interval, function=None):

        Countdown.__init__(self, interval, function)

    def handle_timeout(self):

        super().handle_timeout()
        self.restart()
