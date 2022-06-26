
import pygame
from baopig.pybao.objectutilities import Object
from baopig.time.timer import RepeatingTimer
from .logging import LOGGER
from .clipboard import clipboard


class KeyEvent(Object):

    def __init__(self, event):

        Object.__init__(self, **event.__dict__)
        keyboard.last_event = self

    def __str__(self):
        global __key_events
        return "<KeyEvent({}-{} {})>".format(
            self.type,
            "KEYDOWN" if self.type == pygame.KEYDOWN else "KEYUP" if self.type == pygame.KEYUP else "Unknown",
            self.__dict__
        )


class _Keyboard:

    def __init__(self):

        # self._keys = [0] * 512          # 512 = len(pygame.key.get_pressed())
        self._keys = {}
        self._application = None
        class Mod:  # todo : update
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
            def __str__(self):
                return Object.__str__(self)
        self._mod = Mod()
        self.last_event = None

        # repeat
        self._pressedkeys_timers = {}  # the time when the key have been pressed
        self._is_repeating = False
        self._repeat_first_delay = None
        self._repeat_delay = None

    application = property(lambda self: self._application)
    is_repeating = property(lambda self: self._is_repeating)
    mod = property(lambda self: self._mod)

    def _release_all(self):

        for key in tuple(self._keys):
            self.receive(Object(type=pygame.KEYUP, key=key))

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

        # ACTUALIZING KEYBOARD STATES
        if event.type == pygame.KEYDOWN:
            self._keys[event.key] = 1
            if event.key not in self._pressedkeys_timers:
                self._pressedkeys_timers[event.key] = None
            if self._is_repeating and self._pressedkeys_timers[event.key] is None:
                repeat = RepeatingTimer((self._repeat_first_delay / 1000, self._repeat_delay / 1000),
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
            LOGGER.warning("Unexpected event : {}".format(event))
            return
        KeyEvent(event)  # keyboard.last_event

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

    def set_repeat(self, first_delay, delay):
        """Control how held keys are repeated, with delays in milliseconds"""
        # This solve a bug in pygame, who can't repeat two keys

        assert first_delay >= 0
        assert delay > 0

        if 1 in self._keys:
            raise PermissionError("You must set the keys repeat before launch the application")

        self._is_repeating = True
        self._repeat_first_delay = first_delay
        self._repeat_delay = delay


keyboard = _Keyboard()