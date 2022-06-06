
import pygame
from baopig.pybao.objectutilities import Object
from baopig.time.timer import RepeatingTimer
from .logging import LOGGER
from .clipboard import clipboard


class KeyEvent(Object):

    def __init__(self, event):

        Object.__init__(self, type=event.type, **event.__dict__)
        keyboard.last_event = self

    def __str__(self):
        global __key_events
        return "<KeyEvent({}-{} {})>".format(
            self.type,
            "KEYDOWN" if self.type == keyboard.KEYDOWN else "KEYUP" if self.type == keyboard.KEYUP else "Unknown",
            self.__dict__
        )


class _Keyboard:

    # copied from pygame.constants
    if True:
        KEYDOWN = pygame.KEYDOWN
        KEYUP = pygame.KEYUP

        MOD_ALT = 768
        MOD_CAPS = 8192
        MOD_CTRL = 192
        MOD_LALT = 256
        MOD_LCTRL = 64
        MOD_LMETA = 1024
        MOD_LSHIFT = 1
        MOD_META = 3072
        MOD_MODE = 16384
        MOD_NONE = 0
        MOD_NUM = 4096
        MOD_RALT = 512
        MOD_RCTRL = 128
        MOD_RMETA = 2048
        MOD_RSHIFT = 2
        MOD_SHIFT = 3

        _0 = 48
        _1 = 49
        _2 = 50
        _3 = 51
        _4 = 52
        _5 = 53
        _6 = 54
        _7 = 55
        _8 = 56
        _9 = 57
        a = 97
        AMPERSAND = 38
        ASTERISK = 42
        AT = 64
        b = 98
        BACKQUOTE = 96
        BACKSLASH = 92
        BACKSPACE = 8
        BREAK = 318
        c = 99
        CAPSLOCK = 301
        CARET = 94
        CLEAR = 12
        COLON = 58
        COMMA = 44
        d = 100
        DELETE = 127
        DOLLAR = 36
        DOWN = 274
        e = 101
        END = 279
        EQUALS = 61
        ESCAPE = 27
        EURO = 321
        EXCLAIM = 33
        f = 102
        F1 = 282
        F10 = 291
        F11 = 292
        F12 = 293
        F13 = 294
        F14 = 295
        F15 = 296
        F2 = 283
        F3 = 284
        F4 = 285
        F5 = 286
        F6 = 287
        F7 = 288
        F8 = 289
        F9 = 290
        FIRST = 0
        g = 103
        GREATER = 62
        h = 104
        HASH = 35
        HELP = 315
        HOME = 278
        i = 105
        INSERT = 277
        j = 106
        k = 107
        KP0 = 256
        KP1 = 257
        KP2 = 258
        KP3 = 259
        KP4 = 260
        KP5 = 261
        KP6 = 262
        KP7 = 263
        KP8 = 264
        KP9 = 265

        KP_DIVIDE = 267
        KP_ENTER = 271
        KP_EQUALS = 272
        KP_MINUS = 269
        KP_MULTIPLY = 268
        KP_PERIOD = 266
        KP_PLUS = 270

        l = 108
        LALT = 308
        LAST = 323
        LCTRL = 306
        LEFT = 276
        LEFTBRACKET = 91
        LEFTPAREN = 40
        LESS = 60
        LMETA = 310
        LSHIFT = 304
        LSUPER = 311
        m = 109
        MENU = 319
        MINUS = 45
        MODE = 313
        n = 110
        NUMLOCK = 300
        o = 111
        p = 112
        PAGEDOWN = 281
        PAGEUP = 280
        PAUSE = 19
        PERIOD = 46
        PLUS = 43
        POWER = 320
        PRINT = 316
        q = 113
        QUESTION = 63
        QUOTE = 39
        QUOTEDBL = 34
        r = 114
        RALT = 307
        RCTRL = 305
        RETURN = 13
        RIGHT = 275
        RIGHTBRACKET = 93
        RIGHTPAREN = 41
        RMETA = 309
        RSHIFT = 303
        RSUPER = 312
        s = 115
        SCROLLOCK = 302
        SEMICOLON = 59
        SLASH = 47
        SPACE = 32
        SYSREQ = 317
        t = 116
        TAB = 9
        u = 117
        UNDERSCORE = 95
        UNKNOWN = 0
        UP = 273
        v = 118
        w = 119
        x = 120
        y = 121
        z = 122

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
        self._keys_time = [None] * 323  # the time where the key have been pressed
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
            if self._is_repeating and self._keys_time[event.key] is None:
                repeat = RepeatingTimer((self._repeat_first_delay / 1000, self._repeat_delay / 1000),
                                        pygame.event.post, event)
                repeat.start()
                self._keys_time[event.key] = repeat
        elif event.type == pygame.KEYUP:
            if self._keys[event.key] == 0:
                return  # The KEYDOWN have been skipped, so we skip the KEYUP
            self._keys[event.key] = 0
            if self._is_repeating:
                assert self._keys_time[event.key] is not None
                self._keys_time[event.key].cancel()
                self._keys_time[event.key] = None
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