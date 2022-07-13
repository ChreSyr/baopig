
import pygame
from baopig.communicative import Communicative
from baopig.time.timer import RepeatingTimer
from .logging import LOGGER


class _Keyboard(Communicative):
    _signals = "KEYDOWN", "KEYUP"

    def __init__(self):

        Communicative.__init__(self)

        # 2 signals :
        #     - KEYDOWN
        #     - KEYUP
        for signal in self._signals:
            self.create_signal(signal)

        self._keys = {}
        self._application = None
        self.last_event = None

        class Mod:
            def __init__(self):
                self.l_alt = False
                self.r_alt = False
                self.alt = self.l_alt or self.r_alt
                self.l_cmd = False
                self.r_cmd = False
                self.cmd = self.l_cmd or self.r_cmd
                self.l_ctrl = False
                self.r_ctrl = False
                self.ctrl = self.l_alt or self.r_ctrl
                self.l_maj = False
                self.r_maj = False
                self.maj = self.l_maj or self.r_maj
            # def __str__(self):
            #     return Object.__str__(self)
        self._mod = Mod()

        # repeat
        self._pressedkeys_timers = {}  # the time when the key have been pressed
        self._is_repeating = False
        self._repeat_first_delay = None
        self._repeat_delay = None

        self.set_repeat(.5, .05)

    application = property(lambda self: self._application)
    is_repeating = property(lambda self: self._is_repeating)
    mod = property(lambda self: self._mod)

    def is_pressed(self, key):
        """Return True if the key with identifier 'key' (an integer) is pressed"""

        # You can write bp.keyboard.is_pressed("z")
        if isinstance(key, str):
            key = getattr(self, key)

        try:
            return bool(self._keys[key])
        except KeyError:
            # Here, the key has never been pressed
            return 0

    def receive(self, event):
        """Receive pygame events from the application"""

        self.last_event = event

        # ACTUALIZING KEYBOARD STATES
        if event.type == pygame.KEYDOWN:
            self._keys[event.key] = 1
            if event.key not in self._pressedkeys_timers:
                self._pressedkeys_timers[event.key] = None
            if self._is_repeating and self._pressedkeys_timers[event.key] is None:
                repeat = RepeatingTimer((self._repeat_first_delay, self._repeat_delay),
                                        pygame.event.post, event)
                repeat.start()
                self._pressedkeys_timers[event.key] = repeat
        elif event.type == pygame.KEYUP:
            if self._keys[event.key] == 0:
                return  # The KEYDOWN have been skipped, so we skip the KEYUP
            self._keys[event.key] = 0
            if self._is_repeating:
                assert self._pressedkeys_timers[event.key] is not None
                self._pressedkeys_timers[event.key].cancel()
                self._pressedkeys_timers[event.key] = None
        else:
            LOGGER.warning(f"Unexpected event : {event}")
            return

        if event.key == pygame.K_RALT:
            self.mod.r_alt = event.type == pygame.KEYDOWN
            self.mod.alt = self.mod.l_alt or self.mod.r_alt
        elif event.key == pygame.K_LALT:
            self.mod.l_alt = event.type == pygame.KEYDOWN
            self.mod.alt = self.mod.l_alt or self.mod.r_alt
        elif event.key == pygame.K_RMETA:
            self.mod.r_cmd = event.type == pygame.KEYDOWN
            self.mod.cmd = self.mod.l_cmd or self.mod.r_cmd
        elif event.key == pygame.K_LMETA:
            self.mod.l_cmd = event.type == pygame.KEYDOWN
            self.mod.cmd = self.mod.l_cmd or self.mod.r_cmd
        elif event.key == pygame.K_RCTRL:
            self.mod.r_ctrl = event.type == pygame.KEYDOWN
            self.mod.ctrl = self.mod.l_ctrl or self.mod.r_ctrl
        elif event.key == pygame.K_LCTRL:
            self.mod.l_ctrl = event.type == pygame.KEYDOWN
            self.mod.ctrl = self.mod.l_ctrl or self.mod.r_ctrl
        elif event.key == pygame.K_RSHIFT:
            self.mod.r_maj = event.type == pygame.KEYDOWN
            self.mod.maj = self.mod.l_maj or self.mod.r_maj
        elif event.key == pygame.K_LSHIFT:
            self.mod.l_maj = event.type == pygame.KEYDOWN
            self.mod.maj = self.mod.l_maj or self.mod.r_maj

        # EVENT TRANSMISSION
        for signal_id in self._signals:
            if event.type == getattr(pygame, signal_id):
                getattr(self.signal, signal_id).emit(event)
                break

    def set_repeat(self, first_delay, delay):
        """Control how held keys are repeated, with delays in seconds"""
        # This solves a bug in pygame, who can't repeat two keys

        assert first_delay >= 0
        assert delay > 0

        if 1 in self._keys:
            raise PermissionError("You must set the keys repeat before launch the application")

        self._is_repeating = True
        self._repeat_first_delay = first_delay
        self._repeat_delay = delay


keyboard = _Keyboard()
