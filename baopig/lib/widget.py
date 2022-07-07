# TODO : replace sticky and ref and refloc by flags ?
# TODO : smart to use static, interactive, dynamic ?


import pygame
from baopig.pybao.issomething import *
from baopig.pybao.objectutilities import Object
from baopig.io import mouse
from baopig.documentation import Widget as WidgetDoc
from baopig.communicative import Communicative
from .utilities import paint_lock, MetaPaintLocker
from .style import HasStyle, StyleClass, Theme


class WeakRef:
    def __init__(self, ref):
        self._ref = ref

    def __call__(self):
        return self._ref


class _Origin:
    """
    An Origin is referenced by its parent
    When the parent moves, the widget follows

    An Origin coordinate can be given in different ways:
        - x = 4         sets x to 4 pixels
        - x = '10%'     sets x to self.parent.width * 10 / 100 (automatically updated)

    WARNING : A widget with a dynamic origin (pourcentage position) cannot be manually
              moved by any other way than redefining the origin
    """

    def __init__(self, owner):

        """
        asked_pos is the distance between reference at reference_location and owner at location
        """
        self._asked_pos = owner.style["pos"]
        self._location = owner.style["loc"]
        reference = owner.style["ref"]
        self._reference_location = owner.style["refloc"]
        self._referenced_by_hitbox = owner.style["referenced_by_hitbox"]

        if reference is None:
            reference = owner.parent
        self._owner_ref = owner.get_weakref()
        self._reference_ref = reference.get_weakref()

        self.reference.signal.RESIZE.connect(self._weak_update_owner_pos, owner=self.owner)
        if self.reference != owner.parent:
            self.reference.signal.MOTION.connect(self._weak_update_owner_pos, owner=self.owner)

    def __str__(self):
        return f"Origin(asked_pos={self.asked_pos}, location={self.location}, reference={self.reference}, " \
               f"reference_location={self.reference_location}, referenced_by_hitbox={self.referenced_by_hitbox}, " \
               f"is_locked={self.is_locked})"

    asked_pos = property(lambda self: self._asked_pos)
    referenced_by_hitbox = property(lambda self: self._referenced_by_hitbox)
    is_locked = property(lambda self: self.owner.has_locked("origin"))
    location = property(lambda self: self._location)
    owner = property(lambda self: self._owner_ref())
    reference = property(lambda self: self._reference_ref())
    reference_location = property(lambda self: self._reference_location)

    def _get_sticky(self):
        if self.location == self.reference_location:
            return self.location
        return None

    sticky = property(_get_sticky)

    def _reset_asked_pos(self):
        """
        This method should only be called by Widget._move()
        If the asked_pos was including percentage, and the percentage don't match anymore, it will be
        replaced by an integer value
        """

        old_pos = self.pos
        current_pos = getattr(self.owner.rect, self.location)
        if old_pos == current_pos:
            return

        if self.is_locked:
            raise AssertionError(self)

        owner_abspos_at_location = getattr(self.owner.abs, self.location)
        reference_abspos_at_location = getattr(self.reference.abs, self.reference_location)

        self._asked_pos = (
            owner_abspos_at_location[0] - reference_abspos_at_location[0],
            owner_abspos_at_location[1] - reference_abspos_at_location[1]
        )

    def _weak_update_owner_pos(self):
        if self.owner.is_asleep:
            return
        new_pos = self.pos
        old_pos = getattr(self.owner.rect, self.location)
        if new_pos == old_pos:
            return
        self.owner._move(dx=new_pos[0] - old_pos[0], dy=new_pos[1] - old_pos[1])

    @staticmethod
    def accept(coord):

        if isinstance(coord, str):
            if not coord.endswith('%'):
                return False
            try:
                int(coord[:-1])
                return True
            except ValueError:
                return False

        elif hasattr(coord, "__iter__"):
            if len(coord) != 2: return False
            return False not in (_Origin.accept(c) for c in coord)

        try:
            coord = int(coord)
            return True
        except ValueError:
            raise TypeError("Wrong position value : {} (see documentation above)".format(coord))

    def config(self, pos=None, loc=None, refloc=None, referenced_by_hitbox=None, sticky=None, locked=None):

        if locked is False:
            self.owner.set_lock(origin=False)

        if self.is_locked:
            raise PermissionError("This origin is locked")

        if sticky is not None:
            assert loc is None
            assert refloc is None
            loc = refloc = sticky

        if loc is not None:
            self._location = Location(loc)

        if refloc is not None:
            self._reference_location = Location(refloc)

        if referenced_by_hitbox is not None:
            self._referenced_by_hitbox = bool(referenced_by_hitbox)

        if pos is not None:
            assert _Origin.accept(pos), f"Wrong position value : {pos} (see documentation above)"
            self._asked_pos = pos

        self.owner.move_at(self.pos, self.location)

        if locked is True:
            self.owner.set_lock(origin=True)

    def get_pos_relative_to_owner_parent(self):

        pos = []

        if self.referenced_by_hitbox:

            # Percentage translation of asked_pos
            for i, c in enumerate(self._asked_pos):

                if isinstance(c, str):
                    c = self.reference.hitbox.size[i] * int(c[:-1]) / 100

                pos.append(int(c))

            # Transition at reference_location
            if self._reference_location != "topleft":
                d = getattr(self.reference.auto_hitbox, self._reference_location)
                for i in range(2):
                    pos[i] += d[i]

            # Set pos relative to self.owner.parent
            if self.reference is not self.owner.parent:
                pos = (
                    pos[0] + self.reference.abs_hitbox.left - self.owner.parent.abs.left,
                    pos[1] + self.reference.abs_hitbox.top - self.owner.parent.abs.top
                )

        else:
            # Percentage translation of asked_pos
            for i, c in enumerate(self._asked_pos):

                if isinstance(c, str):
                    c = self.reference.rect.size[i] * int(c[:-1]) / 100

                pos.append(int(c))

            # Transition at reference_location
            if self._reference_location != "topleft":
                dx, dy = getattr(self.reference.auto_rect, self._reference_location)
                pos = pos[0] + dx, pos[1] + dy

            # Set pos relative to self.owner.parent
            if self.reference != self.owner.parent:
                pos = (
                    pos[0] + self.reference.abs.left - self.owner.parent.abs.left,
                    pos[1] + self.reference.abs.top - self.owner.parent.abs.top
                )

        return tuple(pos)

    pos = property(get_pos_relative_to_owner_parent)


class _Window(tuple):
    follow_movements = False


class Location(str):
    ACCEPTED = (
        "topleft", "midtop", "topright",
        "midleft", "center", "midright",
        "bottomleft", "midbottom", "bottomright",
    )

    def __new__(cls, location):
        if location not in Location.ACCEPTED:
            raise ValueError(f"Wrong value for location : '{location}', "
                             f"must be one of {Location.ACCEPTED}")

        return str.__new__(cls, location)


class ProtectedHitbox(pygame.Rect):
    """
    A ProtectedHitbox cannot be resized or moved
    """
    ERR = PermissionError("A ProtectedHitbox cannot change at all")

    def __init__(self, *args, **kwargs):
        pygame.Rect.__init__(self, *args, **kwargs)
        object.__setattr__(self, "_mask", None)

    def __setattr__(self, *args):
        raise self.ERR

    pos = property(lambda self: tuple(self[:2]))
    lpos = property(lambda self: self[:2], doc="A list containing the rect topleft")

    def clamp_ip(self, rect):
        raise self.ERR

    def colliderect(self, rect):
        # TODO : collidemask
        return super().colliderect(rect)

    def inflate_ip(self, x, y):
        raise self.ERR

    def move_ip(self, x, y):
        raise self.ERR

    def referencing(self, pos):
        """
        Return a new pos, relative the hitbox topleft
        The pos is considered as relative to (0, 0)

        Example :
            hibtox = ProtectedHitbox(100, 200, 30, 30)
            pos = (105, 205)
            hitbox.referencing(pos) -> (5, 5)
        """
        return pos[0] - self.left, pos[1] - self.top

    def set_mask(self):
        # TODO : use cases
        raise PermissionError("not implemented yet")

    def union_ip(self, rect):
        raise self.ERR

    def unionall_ip(self, rect_sequence):
        raise self.ERR


class HasProtectedHitbox:
    """
    The pos parameter is in fact the origin, who will often coincide with the topleft
    """
    HITBOX_ATTRIBUTES = (
        "topleft", "midtop", "topright",
        "midleft", "center", "midright",
        "bottomleft", "midbottom", "bottomright",
        "top", "left", "right", "bottom",
        "centerx", "centery", "x", "y",
        "pos",  # pos = topleft
    )

    def __init__(self):
        """
        rect is the surface hitbox, relative to the parent
        abs_rect is the rect relative to the application (also called 'abs')
        auto_rect is the rect relative to the widget itself -> topleft = (0, 0) (also called 'auto')
        window is the rect inside wich the surface can be seen, relative to the parent
        hitbox is the result of clipping rect and window.
        If window is set to None, the hitbox will equal to the rect
        abs_hitbox is the hitbox relative to the application
        auto_hitbox is the hitbox relative to the widget itself
        """

        """
        MOTION is emitted when the absolute position of the widget.rect moves
        It sends two parameters : dx and dy
        WARNING : the dx and dy are the motion of the widget.rect ! This means, when the
                  widget's parent moves, a MOTION.emit(dx=0, dy=0) is probalby raised.
                  In facts, if the widget.origin.reference is not the parent, the motion
                  won't be dx=0, dy=0
        NOTE : an hitbox cannot move and be resized in the same time
        """
        self.create_signal("MOTION")

        """
        Change a surface via set_surface(...) is the only way to change a cmponent size
        Changing size will emit self.signal.RESIZE if the widget is visible
        A widget with locked size cannot be resized, but the surface can change
        
        When a widget is resized, we need a point of reference (called origin) whose pixel
        will not move
        
        origin.location can be one of : topleft,      midtop,     topright,
                                        midleft,      center,     midright,
                                        bottomleft,   midbottom,  bottomright
        
        Example : origin.location = midright
                  if the new size is 10 more pixel on the width, then the origin is on the right,
                  so we add the 10 new pixels to the left 
        """
        self.create_signal("RESIZE")

        # This will initialize the rects and hiboxes
        self._origin = _Origin(owner=self)

        size = self.surface.get_size()
        self._rect = ProtectedHitbox((0, 0), size)
        self._abs_rect = ProtectedHitbox((0, 0), size)
        self._auto_rect = ProtectedHitbox((0, 0), size)
        self._window = None
        self._hitbox = ProtectedHitbox((0, 0), size)
        self._abs_hitbox = ProtectedHitbox((0, 0), size)
        self._auto_hitbox = ProtectedHitbox((0, 0), size)

        # SETUP
        pygame.Rect.__setattr__(self.rect, self.origin.location, self.origin.pos)
        pygame.Rect.__setattr__(self.abs_rect, "topleft",
                                (self.parent.abs.left + self.left, self.parent.abs.top + self.top))
        pygame.Rect.__setattr__(self.hitbox, "topleft", self.topleft)
        pygame.Rect.__setattr__(self.abs_hitbox, "topleft", self.abs.topleft)

    # GETTERS ON PROTECTED FIELDS
    origin = property(lambda self: self._origin)

    # HITBOX
    rect = property(lambda self: self._rect)
    abs = abs_rect = property(lambda self: self._abs_rect)
    auto = auto_rect = property(lambda self: self._auto_rect)
    window = property(lambda self: self._window)
    hitbox = property(lambda self: self._hitbox)
    abs_hitbox = property(lambda self: self._abs_hitbox)
    auto_hitbox = property(lambda self: self._auto_hitbox)

    bottom = property(lambda self: self._rect.bottom, lambda self, v: self.move_at(v, "bottom"))
    bottomleft = property(lambda self: self._rect.bottomleft, lambda self, v: self.move_at(v, "bottomleft"))
    bottomright = property(lambda self: self._rect.bottomright, lambda self, v: self.move_at(v, "bottomright"))
    center = property(lambda self: self._rect.center, lambda self, v: self.move_at(v, "center"))
    centerx = property(lambda self: self._rect.centerx, lambda self, v: self.move_at(v, "centerx"))
    centery = property(lambda self: self._rect.centery, lambda self, v: self.move_at(v, "centery"))
    left = property(lambda self: self._rect.left, lambda self, v: self.move_at(v, "left"))
    midbottom = property(lambda self: self._rect.midbottom, lambda self, v: self.move_at(v, "midbottom"))
    midleft = property(lambda self: self._rect.midleft, lambda self, v: self.move_at(v, "midleft"))
    midright = property(lambda self: self._rect.midright, lambda self, v: self.move_at(v, "midright"))
    midtop = property(lambda self: self._rect.midtop, lambda self, v: self.move_at(v, "midtop"))
    pos = topleft = property(lambda self: self._rect.topleft, lambda self, v: self.move_at(v, "topleft"))
    right = property(lambda self: self._rect.right, lambda self, v: self.move_at(v, "right"))
    top = property(lambda self: self._rect.top, lambda self, v: self.move_at(v, "top"))
    topright = property(lambda self: self._rect.topright, lambda self, v: self.move_at(v, "topright"))
    x = property(lambda self: self._rect.x, lambda self, v: self.move_at(v, "x"))
    y = property(lambda self: self._rect.y, lambda self, v: self.move_at(v, "y"))

    h = property(lambda self: self._rect.h)
    height = property(lambda self: self._rect.height)
    size = property(lambda self: self._rect.size)
    w = property(lambda self: self._rect.w)
    width = property(lambda self: self._rect.width)

    def _move(self, dx, dy):

        if self.is_asleep:
            raise PermissionError("Asleep widgets cannot move")

        old_hitbox = tuple(self.hitbox)
        with paint_lock:

            pygame.Rect.__setattr__(self.rect, "left", self.rect.left + dx)
            pygame.Rect.__setattr__(self.rect, "top", self.rect.top + dy)
            pygame.Rect.__setattr__(self.abs_rect, "topleft",
                                    (self.parent.abs.left + self.left, self.parent.abs.top + self.top))

            if self.window is not None:

                if self.window.follow_movements:
                    self._window = _Window((self.window[0] + dx, self.window[1] + dy) + self.window[2:])
                    self.window.follow_movements = True
                    pygame.Rect.__setattr__(self.hitbox, "topleft", (self.hitbox.left + dx, self.hitbox.top + dy))
                    pygame.Rect.__setattr__(self.abs_hitbox, "topleft",
                                            (self.abs_hitbox.left + dx, self.abs_hitbox.top + dy))
                else:
                    self._hitbox = ProtectedHitbox(self.rect.clip(self.window))
                    pygame.Rect.__setattr__(self.abs_hitbox, "topleft", (
                        self.parent.abs.left + self.hitbox.left, self.parent.abs.top + self.hitbox.top))
                    pygame.Rect.__setattr__(self.auto_hitbox, "topleft",
                                            (self.hitbox.left - self.rect.left, self.hitbox.top - self.rect.top))
                    if old_hitbox[2:] != self.hitbox.size:
                        pygame.Rect.__setattr__(self.abs_hitbox, "size", self.hitbox.size)
                        pygame.Rect.__setattr__(self.auto_hitbox, "size", self.hitbox.size)
            else:
                pygame.Rect.__setattr__(self.hitbox, "topleft", self.topleft)
                pygame.Rect.__setattr__(self.abs_hitbox, "topleft", self.abs.topleft)

            self.signal.MOTION.emit(dx, dy)

            # We reset the asked_pos after the MOTION in order to allow cycles of origin referecing
            self.origin._reset_asked_pos()

            if self.is_visible:
                self.send_display_request(rect=self.hitbox.union(old_hitbox))

    def _update_from_parent_movement(self):

        # Note : paint_lock is hold by the parent
        old_pos = self.origin.pos
        new_pos = getattr(self.rect, self.origin.location)
        if self._has_locked.origin:
            self.set_lock(origin=False)
            self._move(dx=old_pos[0] - new_pos[0], dy=old_pos[1] - new_pos[1])
            self.set_lock(origin=True)
        else:
            self._move(dx=old_pos[0] - new_pos[0], dy=old_pos[1] - new_pos[1])

    def collidemouse(self):

        return self.is_visible & self.abs_hitbox.collidepoint(mouse.pos)

    def move(self, dx=0, dy=0):

        if dx == 0 and dy == 0:
            return
        if self._has_locked.origin:
            return
        self._move(dx, dy)

    def move_at(self, value, key="topleft"):

        accepted = (
            "x", "y", "centerx", "centery", "top", "bottom", "left", "right", "topleft", "midtop", "topright",
            "midleft",
            "center", "midright", "bottomleft", "midbottom", "bottomright")
        assert key in accepted, f"key '{key}' is not a valid rect position (one of {accepted})"

        if self._has_locked.origin:
            return

        old = getattr(self.rect, key)

        if old == value:
            return

        if isinstance(value, (int, float)):

            if key in ("x", "centerx", "left", "right"):
                self._move(value - old, 0)
            else:
                self._move(0, value - old)

        else:
            self._move(value[0] - old[0], value[1] - old[1])

    def set_window(self, window, follow_movements=None):
        """window is a rect relative to the parent

        follow_movements default to False"""

        if window is not None:
            if window == self.window: return
            assert is_typed_iterable(window, int, 4) or isinstance(window, pygame.Rect), \
                "Wrong recstyle object : {}".format(window)
            self._window = _Window(window)
            if follow_movements is not None:
                self._window.follow_movements = bool(follow_movements)

            old_pos = self.hitbox.topleft
            old_size = self.hitbox.size
            self._hitbox = ProtectedHitbox(self.rect.clip(self.window))
            pygame.Rect.__setattr__(self.abs_hitbox, "topleft",
                                    (self.parent.abs.left + self.hitbox.left, self.parent.abs.top + self.hitbox.top))
            # NOTE : should auto_hitbox.topleft be (0, 0) or the difference between self.pos and self.window.topleft ?
            pygame.Rect.__setattr__(self.auto_hitbox, "topleft",
                                    (self.hitbox.left - self.rect.left, self.hitbox.top - self.rect.top))
            pygame.Rect.__setattr__(self.abs_hitbox, "size", self.hitbox.size)
            pygame.Rect.__setattr__(self.auto_hitbox, "size", self.hitbox.size)

            if old_pos != self.hitbox.topleft:
                self.signal.MOTION.emit(self.left - old_pos[0], self.top - old_pos[1])
            if old_size != self.size:
                self.signal.RESIZE.emit(old_size)

        else:
            self._window = None

        self.send_display_request(rect=self.rect)  # rect is to cover all possibilities

    def update_pos(self):

        if self.is_asleep:  # the widget has no parent
            return

        new_pos = self.origin.pos
        old_pos = getattr(self.rect, self.origin.location)
        if new_pos == old_pos:
            return
        self._move(dx=new_pos[0] - old_pos[0], dy=new_pos[1] - old_pos[1])


class HasProtectedSurface:

    def __init__(self, surface):

        assert isinstance(surface, pygame.Surface)

        """
        surface is the widget's image

        Duing the widget life, the size of surface can NOT differ from
        the size of the hitbox, it is protected thanks to this classe methods and ProtectedSurface
        
        NEW_SURF is emitted right after set_surface()
        """
        self._surface = surface
        self.create_signal("NEW_SURF")

    surface = property(lambda self: self._surface)

    def _set_surface(self, surface):

        with paint_lock:
            self._surface = surface
            size = surface.get_size()
            pygame.Rect.__setattr__(self.rect, "size", size)
            pygame.Rect.__setattr__(self.abs_rect, "size", size)
            pygame.Rect.__setattr__(self.auto_rect, "size", size)
            if self.window:
                size = self.rect.clip(self.window).size
            pygame.Rect.__setattr__(self.hitbox, "size", size)
            pygame.Rect.__setattr__(self.abs_hitbox, "size", size)
            pygame.Rect.__setattr__(self.auto_hitbox, "size", size)
            self.update_pos()

    def set_surface(self, surface):

        assert isinstance(surface, pygame.Surface), surface

        if self._has_locked.height and self.rect.height != surface.get_height():
            raise PermissionError(
                "Wrong surface : {} (this widget's surface height is locked at {})".format(surface, self.h))

        if self._has_locked.width and self.rect.width != surface.get_width():
            raise PermissionError(
                "Wrong surface : {} (this widget's surface width is locked at {})".format(surface, self.w))

        with paint_lock:
            if self.rect.size != surface.get_size():

                old_hitbox = tuple(self.hitbox)
                old_size = self.rect.size
                self._set_surface(surface)
                self.signal.RESIZE.emit(old_size)

                if self.is_visible:
                    self.send_display_request(rect=self.hitbox.union(old_hitbox))

            else:

                self._surface = surface
                if self.is_visible:
                    self.send_display_request()

            self.signal.NEW_SURF.emit()


class Widget(WidgetDoc, HasStyle, Communicative, HasProtectedSurface, HasProtectedHitbox, metaclass=MetaPaintLocker):
    STYLE = HasStyle.STYLE
    STYLE.create(
        pos=(0, 0),
        loc="topleft",
        ref=None,  # default is parent
        refloc="topleft",
        referenced_by_hitbox=False,
    )
    STYLE.set_type("loc", Location)
    STYLE.set_type("refloc", Location)

    def __init__(self, parent, surface=None, layer=None, layer_level=None, name=None, row=None, col=None,
                 visible=True, touchable=True, **kwargs):

        if hasattr(self, "_weakref"):  # Widget.__init__() has already been called
            return

        if name is None:
            name = "NoName"
        if isinstance(layer, str):
            layer = parent.layers_manager.get_layer(layer)

        assert hasattr(parent, "_warn_change")
        assert isinstance(name, str)
        assert surface is not None

        # name is a string who may help to identify the widget
        # It is defined here, so it's in first place in self.__dict__ (should)
        self._name = name

        HasStyle.__init__(self, parent, options=kwargs)
        Communicative.__init__(self)
        HasProtectedSurface.__init__(self, surface)

        # NOTE : Since self is a parent's child, it doesn't need to use a weakref
        self._parent = parent
        self._app = parent.app

        # weakref will return None after widget.kill()
        self._weakref = WeakRef(self)

        # Visibility
        self._is_visible = visible
        self.create_signal("SHOW")
        self.create_signal("HIDE")

        # Sleep
        self._is_asleep = False
        self._sleep_parent_ref = lambda: None
        self.create_signal("SLEEP")
        self.create_signal("WAKE")

        # Locks
        self._has_locked = Object(
            origin=False,
            width=False,
            height=False,
            size=False,
            visibility=False,
        )

        self.create_signal("KILL")

        # NOTE : Since self is a scene's child, it doesn't need to use a weakref
        self.__scene = parent.scene

        self._col = None
        self._row = None
        if (col is not None) or (row is not None):
            """col and row attributes are dedicated to GridLayer"""
            if (self.style["pos"] != (0, 0)) or \
                    (self.style["ref"] is not None) or \
                    (self.style["refloc"] != "topleft"):
                raise PermissionError("When the layer manages the widget's position, "
                                      "all you can define is row, col and loc")
            if col is None:
                col = 0
            if row is None:
                row = 0
            assert isinstance(col, int) and col >= 0
            assert isinstance(row, int) and row >= 0
            self._col = col
            self._row = row

        # sticky is a shortcut :
        #     sticky="center" <=> loc="center", refloc="center"
        if "sticky" in kwargs:
            assert self.style["loc"] == self.style["refloc"] == "topleft", \
                "Cannot use parameter sticky with parameters loc and refloc"
            sticky = Location(kwargs.pop("sticky"))
            self.style.modify(loc=sticky, refloc=sticky)

        # other shortcuts :
        #     center=(200, 45) <=> pos=(200, 45), loc="center"
        # Works for every location
        for key in tuple(kwargs.keys()):
            if key in HasProtectedHitbox.HITBOX_ATTRIBUTES:
                assert self.style["pos"] == (0, 0) and self.style["loc"] == "topleft", \
                    "Cannot use location shortcut with parameters pos and loc"
                location = key
                self.style.modify(pos=kwargs.pop(key), loc=location)
                break  # TODO : error if more than only one key

        # LAYOUT
        if layer is None:
            if parent is not self:  # scene prevention
                layer = parent.layers_manager.find_layer_for(self, layer_level)
        elif layer_level is not None:
            raise PermissionError("Cannot define a layer AND a layer_level")
        self._layer = layer

        # INITIALIZATIONS
        HasProtectedHitbox.__init__(self)
        parent._add_child(self)

        if touchable is False:
            self.set_nontouchable()

        if kwargs:
            raise ValueError(f"Unused options : {kwargs}")

    def __repr__(self):
        """
        Called by repr(self)

        :return: str
        """
        # This complicated string creation is avoiding the o.__repr__()
        # in order to avoid representation of widgets
        return f"<{self.__class__.__name__}(name='{self.name}', parent='{self.parent.name}', hitbox={self.hitbox})>"

    def __str__(self):
        """
        Called by str(self)
        """
        return f"{self.__class__.__name__}(name={self.name})"

    # GETTERS ON PROTECTED FIELDS
    app = application = property(lambda self: self._app)  # TODO : remove application ?
    col = property(lambda self: self._col)
    is_alive = property(lambda self: self._weakref._ref is not None)
    is_asleep = property(lambda self: self._is_asleep)
    is_awake = property(lambda self: not self._is_asleep)
    is_dead = property(lambda self: self._weakref._ref is None)
    is_hidden = property(lambda self: not self._is_visible)
    is_visible = property(lambda self: self._is_visible)
    layer = property(lambda self: self._layer)
    name = property(lambda self: self._name)
    parent = property(lambda self: self._parent)
    row = property(lambda self: self._row)
    scene = property(lambda self: self.__scene)

    def get_weakref(self, callback=None):
        """
        A weakref is a reference to an object
        callback is a function called when the widget die

        Example :
            weak_ref = my_widget.get_weakref()
            my_widget2 = weak_ref()
            my_widget is my_widget2 -> return True
            del my_widget
            print(my_widget2) -> return None
        """
        if callback is not None:
            assert callable(callback)
            self.signal.KILL.connect(callback, owner=None)
        return self._weakref

    def has_locked(self, key):

        try:
            return getattr(self._has_locked, key)
        except AttributeError:
            raise KeyError(f"Unknown key: {key}, availible keys are:{tuple(self._has_locked.__dict__.keys())}")

    def hide(self):

        if self._has_locked.visibility:
            return

        if not self.is_visible:
            return

        self._is_visible = False

        # TODO : the mouse manages itself
        #  -> mouse.focused_widget.signal.HIDE
        #  -> mouse.linked_widget.signal.HIDE
        #  -> mouse.linked_widget.signal.SLEEP
        if self == mouse.linked_widget:
            mouse._unlink()

        self.send_display_request()
        self.signal.HIDE.emit()

    def kill(self):

        if not self.is_alive:
            return

        with paint_lock:
            self.signal.KILL.emit(self._weakref)
            if self.parent is not None:  # False when called by Widget.wake()
                self.parent._remove_child(self)
            self.disconnect()
            self._weakref._ref = None

        del self

    def send_display_request(self, rect=None):

        if self._parent is not None:  # False when asleep
            if rect is None:
                rect = self.hitbox
            self._parent._warn_change(rect)

    def set_lock(self, **kwargs):
        """
        In kwargs, keys can be:
            height
            width
            size
            visibility
            origin
        In kwargs, values are interpreted as booleans
        """
        for key, locked in kwargs.items():
            if not hasattr(self._has_locked, key):
                raise KeyError(f"Unknown key: {key}, availible keys are:{tuple(self._has_locked.__dict__.keys())}")

            self._has_locked.__setattr__(key, bool(locked))
            if key in ("height", "width"):
                self._has_locked.size = self._has_locked.height and self._has_locked.width
            elif key == "size":
                self._has_locked.height = bool(locked)
                self._has_locked.width = bool(locked)

    def set_nontouchable(self):
        """Cannot go back"""

        # TODO : documentation
        # TODO : rework
        # TODO : if Hoverable, mouse.update_hovered_widget() ?
        self.collidemouse = lambda: False

    def show(self):

        if self._has_locked.visibility:
            return
        if self.is_visible:
            return

        self._is_visible = True
        self.send_display_request()
        self.signal.SHOW.emit()

    def sleep(self):

        if self.is_asleep:
            return

        assert self in self.parent.children

        self.parent._remove_child(self)
        self._sleep_parent_ref = self.parent.get_weakref()
        self._parent = None
        self._is_asleep = True
        self.signal.SLEEP.emit()

    def wake(self):

        if self.is_awake:
            return

        self._parent = self._sleep_parent_ref()
        self._sleep_parent_ref = lambda: None
        if self.parent is None:
            return self.kill()

        self._is_asleep = False
        self.parent._add_child(self)
        self.origin._weak_update_owner_pos()
        self.signal.WAKE.emit()

    # TODO : move these methods to Layer
    def move_behind(self, widget):

        self.layer.move_widget1_behind_widget2(widget1=self, widget2=widget)

    def move_in_front_of(self, widget):

        self.layer.move_widget1_in_front_of_widget2(widget1=self, widget2=widget)

    def swap_layer(self, layer):

        if isinstance(layer, str):
            layer = self.parent.layers_manager.get_layer(layer)
        self.parent.layers_manager.swap_layer(self, layer)
