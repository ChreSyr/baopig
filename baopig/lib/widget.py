
# TODO : smart to use static, interactive, dynamic ?

import pygame
from baopig.io import mouse
from baopig.documentation import Widget as WidgetDoc
from baopig.communicative import Communicative
from .utilities import paint_lock, MetaPaintLocker
from .style import HasStyle


class WeakRef:
    def __init__(self, ref):
        self._ref = ref

    def __call__(self):
        return self._ref


class _PosManager:
    """
    An Origin is referenced by its parent
    When the parent moves, the widget follows

    An Origin coordinate can be given in different ways:
        - x = 4         sets x to 4 pixels
        - x = '10%'     sets x to self.parent.width * 10 / 100 (automatically updated)

    WARNING : A widget with a dynamic position (pourcentage position) cannot be manually
              moved by any other way than redefining the WTF ?? TODO
    """

    def __init__(self, owner):

        # asked_pos is the distance between reference at reference_location and owner at location
        self._asked_pos = owner.style["pos"]
        self._location = owner.style["loc"]
        reference = owner.style["ref"]
        self._reference_location = owner.style["refloc"]
        self._referenced_by_hitbox = owner.style["referenced_by_hitbox"]

        if reference is None:
            reference = owner.parent
        self._owner_ref = owner.get_weakref()
        self._reference_ref = reference.get_weakref()

    def __str__(self):
        return f"Origin(asked_pos={self.asked_pos}, location={self.location}, reference={self.reference}, " \
               f"reference_location={self.reference_location}, referenced_by_hitbox={self.referenced_by_hitbox}, " \
               f"is_locked={self.is_locked})"

    asked_pos = property(lambda self: self._asked_pos)
    referenced_by_hitbox = property(lambda self: self._referenced_by_hitbox)
    is_locked = property(lambda self: self.owner.has_locked("pos"))
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

        old_pos = self.get_pos_relative_to_owner_parent()
        current_pos = getattr(self.owner.rect, self.location)
        if old_pos == current_pos:
            return

        if self.is_locked:
            raise AssertionError(self)

        owner_abspos_at_location = getattr(self.owner.abs_rect, self.location)
        reference_abspos_at_location = getattr(self.reference.abs_rect, self.reference_location)

        self._asked_pos = (
            owner_abspos_at_location[0] - reference_abspos_at_location[0],
            owner_abspos_at_location[1] - reference_abspos_at_location[1]
        )

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
            if len(coord) != 2:
                return False
            return False not in (_PosManager.accept(c) for c in coord)

        try:
            coord = int(coord)
            return True
        except ValueError:
            raise TypeError("Wrong position value : {} (see documentation above)".format(coord))

    def config(self, pos=None, loc=None, refloc=None, referenced_by_hitbox=None, sticky=None, locked=None):

        if locked is False:
            self.owner.set_lock(pos=False)

        if self.is_locked:
            raise PermissionError("This widget's position is locked")

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
            assert _PosManager.accept(pos), f"Wrong position value : {pos} (see documentation above)"
            self._asked_pos = pos

        self.owner._update_pos()

        if locked is True:
            self.owner.set_lock(pos=True)

    def get_pos_relative_to_owner_parent(self):

        pos = []

        rect = "hitbox" if self.referenced_by_hitbox else "rect"

        # Percentage translation of asked_pos
        ref_rect = getattr(self.reference, rect)
        for i, c in enumerate(self._asked_pos):
            if isinstance(c, str):
                c = ref_rect.size[i] * float(c[:-1]) / 100
            pos.append(int(c))

        # Transition at reference_location
        if self._reference_location != "topleft":
            ref_autorect = getattr(self.reference, "auto_" + rect)
            d = getattr(ref_autorect, self._reference_location)
            for i in range(2):
                pos[i] += d[i]

        # Set pos relative to self.owner.parent
        if self.reference is not self.owner.parent:
            ref_absrect = getattr(self.reference, "abs_" + rect)
            pos = (
                pos[0] + ref_absrect.left - self.owner.parent.abs_rect.left,
                pos[1] + ref_absrect.top - self.owner.parent.abs_rect.top
            )

        return tuple(pos)

    pos = property(get_pos_relative_to_owner_parent)


class _Window:

    def __init__(self, owner):

        self._owner = owner

        self._is_following_movements = True
        self._is_set = False
        self._offset = (0, 0)  # referenced from owner
        self._size = owner.rect.size
        self._surface = None

        # self._update_surface_TBR()

    is_following_movements = property(lambda self: self._is_following_movements)
    is_set = property(lambda self: self._is_set)
    offset = property(lambda self: self._offset)
    size = property(lambda self: self._size)
    surface = property(lambda self: self._surface)

    def _update_surface_TBR(self):

        subsurface_rect = self._owner.auto_rect.clip(self._offset + self.size)
        self._surface = self._owner.surface.subsurface(subsurface_rect)

    def config(self, offset=None, size=None):

        if offset is not None:
            self._offset = tuple(offset)

        if size is not None:
            self._size = tuple(size)

        # self._update_surface_TBR()

    def get_hitbox(self):

        offset_refed_from_owner_parent = (
            self._offset[0] + self._owner.rect.left,
            self._offset[1] + self._owner.rect.top,
        )

        return pygame.Rect(offset_refed_from_owner_parent, self._size).clip(self._owner.rect)

        return offset_refed_from_owner_parent + self._size


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

    def __setattr__(self, *args):
        raise self.ERR

    pos = property(lambda self: tuple(self[:2]))

    def clamp_ip(self, rect):
        raise self.ERR

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

    def union_ip(self, rect):
        raise self.ERR

    def unionall_ip(self, rect_sequence):
        raise self.ERR


class WidgetCore(WidgetDoc, Communicative):

    def __init__(self, parent):
        assert hasattr(parent, "_warn_change")

        Communicative.__init__(self)

        # NOTE : Since self is a parent's child, it doesn't need to use weakrefs
        self._parent = parent
        self.__scene = parent.scene
        self._application = parent.application

        # weakref will return None after widget.kill()
        self._weakref = WeakRef(self)
        self.create_signal("KILL")

    application = property(lambda self: self._application)
    parent = property(lambda self: self._parent)
    scene = property(lambda self: self.__scene)

    is_alive = property(lambda self: self._weakref() is not None)
    is_dead = property(lambda self: self._weakref() is None)

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

    def kill(self):

        if not self.is_alive:
            return

        with paint_lock:
            if self.parent is not None:  # False when called by Widget.wake()
                self.parent._remove_child(self)
            self.signal.KILL.emit(self._weakref)
            self.disconnect()
            self._weakref._ref = None

        del self


class HasLock:  # TODO : remove

    def __init__(self):

        class Locks:
            pos = False
            width = False
            height = False
            size = False
            visibility = False

        self._has_locked = Locks()

    def has_locked(self, key):

        try:
            return getattr(self._has_locked, key)
        except AttributeError:
            raise KeyError(f"Unknown key: {key}, availible keys are:{tuple(self._has_locked.__dict__.keys())}")

    def set_lock(self, **kwargs):
        """
        In kwargs, keys can be:
            pos
            width
            height
            size
            visibility
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


class Widget_VisibleSleepy(WidgetCore, HasLock):

    def __init__(self, parent):

        WidgetCore.__init__(self, parent)
        HasLock.__init__(self)

        # Sleep
        self._is_asleep = False
        self._sleep_parent_ref = lambda: ...
        self.create_signal("SLEEP")
        self.create_signal("WAKE")

        # Visibility
        self._is_visible = True
        self.create_signal("SHOW")
        self.create_signal("HIDE")

    is_asleep = property(lambda self: self._is_asleep)
    is_awake = property(lambda self: not self._is_asleep)
    is_hidden = property(lambda self: not self._is_visible)
    is_visible = property(lambda self: self._is_visible)

    def hide(self):

        if self._has_locked.visibility:
            return

        if not self.is_visible:
            return

        self._is_visible = False

        self.send_display_request()
        self.signal.HIDE.emit()

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

        if self in self.parent.children:  # False when called during construction
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
        self.signal.WAKE.emit()


class TouchableByMouse:

    def __init__(self, touchable):
        self._is_touchable_by_mouse = touchable

    is_touchable_by_mouse = property(lambda self: self._is_touchable_by_mouse)

    def set_touchable_by_mouse(self, val):
        self._is_touchable_by_mouse = bool(val)


class HasProtectedHitbox(Widget_VisibleSleepy, HasStyle, TouchableByMouse):
    STYLE = HasStyle.STYLE
    STYLE.create(
        pos=(0, 0),
        loc="topleft",
        ref=None,  # default is parent
        refloc="topleft",
        referenced_by_hitbox=False,
        width=None,  # must be filled
        height=None,  # must be filled
    )
    STYLE.set_type("loc", Location)
    STYLE.set_type("refloc", Location)

    def __init__(self, parent, size, touchable=True, **kwargs):
        """
        rect is the surface hitbox, relative to the parent
        abs_rect is the rect relative to the application
        auto_rect is the rect relative to the widget itself -> topleft = (0, 0)
        window is the rect inside wich the surface can be seen, relative to the parent
        hitbox is the result of clipping rect and window.
        If window is set to None, the hitbox will equal to the rect
        abs_hitbox is the hitbox relative to the application
        auto_hitbox is the hitbox relative to the widget itself
        """

        Widget_VisibleSleepy.__init__(self, parent)
        HasStyle.__init__(self, parent, options=kwargs)
        TouchableByMouse.__init__(self, touchable)

        # Shortcuts :                                             - NOTE : Can only use one shortcut
        #   sticky="center"   <=>  loc="center", refloc="center"
        #   center=(200, 45)  <=>  pos=(200, 45), loc="center"    - works for every location
        if "sticky" in kwargs:
            sticky = Location(kwargs.pop("sticky"))
            self.style.modify(loc=sticky, refloc=sticky)
        else:
            for key in tuple(kwargs.keys()):
                if key in Location.ACCEPTED:
                    self.style.modify(pos=kwargs.pop(key), loc=key)
                    break

        if kwargs:
            raise ValueError(f"Unused options : {kwargs}")

        """
        MOTION is emitted when the absolute position of the widget.rect moves
        It sends two parameters : dx and dy
        WARNING : the dx and dy are the motion of the widget.rect ! This means, when the
                  widget's parent moves, a MOTION.emit(dx=0, dy=0) is probalby raised.
                  In facts, if the widget.pos_manager.reference is not the parent, the motion
                  won't be dx=0, dy=0
        NOTE : an hitbox cannot move and be resized in the same time
        """
        self.create_signal("MOTION")

        """
        Change a surface via set_surface(...) is the only way to change a cmponent size
        Changing size will emit self.signal.RESIZE if the widget is visible
        A widget with locked size cannot be resized, but the surface can change
        
        When a widget is resized, we need a point of reference (called location) whose pixel
        will not move
        
        pos_manager.location can be one of : topleft,      midtop,     topright,
                                             midleft,      center,     midright,
                                             bottomleft,   midbottom,  bottomright
        
        Example : pos_manager.location = midright
                  if the new size is 10 more pixel on the width, then the position is on the right,  TODO
                  so we add the 10 new pixels to the left 
        """
        self.create_signal("RESIZE")

        # This will initialize the rects and hiboxes
        self._pos_manager = _PosManager(owner=self)

        self._rect = ProtectedHitbox((0, 0), size)
        self._abs_rect = ProtectedHitbox((0, 0), size)
        self._auto_rect = ProtectedHitbox((0, 0), size)
        self._window = _Window(self)
        self._hitbox = ProtectedHitbox((0, 0), size)
        self._abs_hitbox = ProtectedHitbox((0, 0), size)
        self._auto_hitbox = ProtectedHitbox((0, 0), size)

        # SETUP
        pygame.Rect.__setattr__(self.rect, self._pos_manager.location, self._pos_manager.pos)
        pygame.Rect.__setattr__(self.abs_rect, "topleft",
                                (self.parent.abs_rect.left + self.rect.left, self.parent.abs_rect.top + self.rect.top))
        pygame.Rect.__setattr__(self.hitbox, "topleft", self.rect.topleft)
        pygame.Rect.__setattr__(self.abs_hitbox, "topleft", self.abs_rect.topleft)

        # Connections
        self.signal.WAKE.connect(self._update_pos, owner=self)
        pos_ref = self._pos_manager.reference
        pos_ref.signal.RESIZE.connect(self._update_pos, owner=self)
        if pos_ref != self.parent:
            pos_ref.signal.MOTION.connect(self._update_pos, owner=self)

        def update_pos_from_parent_movement():
            # Code from _update_pos(), without these two lines:
            #     if new_pos == old_pos:
            #       return
            # This allows the MOTION.emit() even if no movement has been made
            # This way, widgets referenced by this widget can update their positions
            if self.is_asleep:  # the widget has no parent
                return
            new_pos = self._pos_manager.get_pos_relative_to_owner_parent()
            rect = self.hitbox if self._pos_manager.referenced_by_hitbox else self.rect
            old_pos = getattr(rect, self._pos_manager.location)
            self._move(dx=new_pos[0] - old_pos[0], dy=new_pos[1] - old_pos[1])

        self.parent.signal.MOTION.connect(update_pos_from_parent_movement, owner=self)

    # ORIGIN
    pos_manager = property(lambda self: self._pos_manager)

    # HITBOX
    rect = property(lambda self: self._rect)
    abs_rect = property(lambda self: self._abs_rect)
    auto_rect = property(lambda self: self._auto_rect)
    window = property(lambda self: self._window)
    hitbox = property(lambda self: self._hitbox)
    abs_hitbox = property(lambda self: self._abs_hitbox)
    auto_hitbox = property(lambda self: self._auto_hitbox)

    def _move(self, dx, dy):

        if self.is_asleep:
            raise PermissionError("Asleep widgets cannot move")

        old_hitbox = tuple(self.hitbox)
        with paint_lock:

            pygame.Rect.__setattr__(self.rect, "left", self.rect.left + dx)
            pygame.Rect.__setattr__(self.rect, "top", self.rect.top + dy)
            pygame.Rect.__setattr__(self.abs_rect, "topleft", (self.parent.abs_rect.left + self.rect.left,
                                                               self.parent.abs_rect.top + self.rect.top))

            if self.window.is_set:

                if self.window.is_following_movements:
                    pygame.Rect.__setattr__(self.hitbox, "topleft", (self.hitbox.left + dx, self.hitbox.top + dy))
                    pygame.Rect.__setattr__(self.abs_hitbox, "topleft",
                                            (self.abs_hitbox.left + dx, self.abs_hitbox.top + dy))
                else:
                    self._window.config(offset=(self.window.offset[0] - dx, self.window.offset[1] - dy))
                    self._hitbox = ProtectedHitbox(self.window.get_hitbox())
                    pygame.Rect.__setattr__(self.abs_hitbox, "topleft", (
                        self.parent.abs_rect.left + self.hitbox.left, self.parent.abs_rect.top + self.hitbox.top))
                    pygame.Rect.__setattr__(self.auto_hitbox, "topleft",
                                            (self.hitbox.left - self.rect.left, self.hitbox.top - self.rect.top))
                    if old_hitbox[2:] != self.hitbox.size:
                        pygame.Rect.__setattr__(self.abs_hitbox, "size", self.hitbox.size)
                        pygame.Rect.__setattr__(self.auto_hitbox, "size", self.hitbox.size)
            else:
                pygame.Rect.__setattr__(self.hitbox, "topleft", self.rect.topleft)
                pygame.Rect.__setattr__(self.abs_hitbox, "topleft", self.abs_rect.topleft)

            # We reset the asked_pos after the MOTION in order to allow cycles of pos referecing  TODO
            self._pos_manager._reset_asked_pos()

            if self.is_visible:
                self.send_display_request(rect=self.hitbox.union(old_hitbox))

            self.signal.MOTION.emit(dx, dy)

    def _move_at(self, key, value):

        accepted = (
            "x", "y", "centerx", "centery", "top", "bottom", "left", "right", "topleft", "midtop", "topright",
            "midleft", "center", "midright", "bottomleft", "midbottom", "bottomright")
        assert key in accepted, f"key '{key}' is not a valid rect position (one of {accepted})"

        if self._has_locked.pos:
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

    def _update_pos(self):
        """ Updates the postion from pos_manager's values """

        if self.is_asleep:  # the widget has no parent
            return

        self._move_at(key=self.pos_manager.location, value=self.pos_manager.get_pos_relative_to_owner_parent())

    def collidemouse(self):

        return self.is_visible and self.abs_hitbox.collidepoint(mouse.pos)

    def move(self, dx=0, dy=0):

        if dx == 0 and dy == 0:
            return
        if self._has_locked.pos:
            return
        self._move(dx, dy)

    def send_display_request(self, rect=None):

        if self._parent is not None:  # False when asleep
            if rect is None:
                rect = self.hitbox
            self._parent._warn_change(rect)

    def set_pos(self, **kwarg):
        """ Example : my_widget.set_pos(midtop=(50, 10) """

        assert len(kwarg) == 1
        self._move_at(*kwarg.popitem())

    def set_window(self, window, follow_movements):  # TODO : refed from self
        """window is a rect relative to the parent

        follow_movements default to False"""

        self.window._is_set = window is not None
        if window is None:
            self.window.config(offset=(0, 0), size=self.rect.size)
        else:
            offset_from_parent = window[:2]
            offset_from_self = (
                offset_from_parent[0] - self.rect.left,
                offset_from_parent[1] - self.rect.top
            )
            self.window.config(offset=offset_from_self, size=window[2:])

            self.window._is_following_movements = bool(follow_movements)

            old_pos = self.rect.topleft
            old_size = self.rect.size
            self._hitbox = ProtectedHitbox(self.window.get_hitbox())
            pygame.Rect.__setattr__(self.abs_hitbox, "topleft", (self.parent.abs_rect.left + self.hitbox.left,
                                                                 self.parent.abs_rect.top + self.hitbox.top))
            # NOTE : should auto_hitbox.topleft be (0, 0) or the difference between self.pos and self.window.topleft ?
            pygame.Rect.__setattr__(self.auto_hitbox, "topleft",
                                    (self.hitbox.left - self.rect.left, self.hitbox.top - self.rect.top))
            pygame.Rect.__setattr__(self.abs_hitbox, "size", self.hitbox.size)
            pygame.Rect.__setattr__(self.auto_hitbox, "size", self.hitbox.size)

            if old_pos != self.rect.topleft:
                self.signal.MOTION.emit(self.rect.left - old_pos[0], self.rect.top - old_pos[1])
            if old_size != self.rect.size:
                self.signal.RESIZE.emit(old_size)

        self.send_display_request(rect=self.rect)  # rect covers all possibilities


class HasProtectedSurface(HasProtectedHitbox):

    def __init__(self, parent, surface, **kwargs):

        assert isinstance(surface, pygame.Surface)

        HasProtectedHitbox.__init__(self, parent, surface.get_size(), **kwargs)

        """
        surface is the widget's image

        Duing the widget life, the size of surface can NOT differ from
        the size of the hitbox, it is protected thanks to this classe methods and ProtectedSurface
        
        NEW_SURFACE is emitted right after set_surface()
        """
        self._surface = surface
        self.create_signal("NEW_SURFACE")

    surface = property(lambda self: self._surface)

    def _update_size_from_newsurface(self, size):

        with paint_lock:
            pygame.Rect.__setattr__(self.rect, "size", size)
            pygame.Rect.__setattr__(self.abs_rect, "size", size)
            pygame.Rect.__setattr__(self.auto_rect, "size", size)
            if self.window.is_set:
                size = self.window.get_hitbox().size
            pygame.Rect.__setattr__(self.hitbox, "size", size)
            pygame.Rect.__setattr__(self.abs_hitbox, "size", size)
            pygame.Rect.__setattr__(self.auto_hitbox, "size", size)
            self._update_pos()

    def set_surface(self, surface):

        assert isinstance(surface, pygame.Surface), surface

        if self._has_locked.height and self.rect.height != surface.get_height():
            raise PermissionError(
                f"Wrong surface : {surface} (this widget's surface height is locked at {self.rect.h})")

        if self._has_locked.width and self.rect.width != surface.get_width():
            raise PermissionError(
                f"Wrong surface : {surface} (this widget's surface width is locked at {self.rect.w})")

        with paint_lock:
            if self.rect.size != surface.get_size():

                old_hitbox = tuple(self.hitbox)
                old_size = self.rect.size
                self._surface = surface
                self._update_size_from_newsurface(surface.get_size())
                self.signal.RESIZE.emit(old_size)

                if self.is_visible:
                    self.send_display_request(rect=self.hitbox.union(old_hitbox))

            else:

                self._surface = surface
                if self.is_visible:
                    self.send_display_request()

            self.signal.NEW_SURFACE.emit()


class Widget(HasProtectedSurface, metaclass=MetaPaintLocker):

    def __init__(self, parent, layer=None, layer_level=None, name=None, row=None, col=None,
                 visible=True, **kwargs):

        if hasattr(self, "_weakref"):  # Widget.__init__() has already been called
            return

        # name is a string who may help to identify the widget
        # It is defined here, so it's in first place in self.__dict__ (should)
        self._name = name if name else "NoName"

        # INITIALIZATIONS
        HasProtectedSurface.__init__(self, parent, **kwargs)

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

        # LAYOUT
        if layer is None:
            if parent is not self:  # scene prevention
                layer = parent.layers_manager.find_layer_for(self, layer_level)
        elif layer_level is not None:
            raise PermissionError("Cannot define a layer AND a layer_level")
        elif isinstance(layer, str):
            layer = parent.layers_manager.get_layer(layer)
        self._layer = layer

        self._is_visible = visible

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
    col = property(lambda self: self._col)
    layer = property(lambda self: self._layer)
    name = property(lambda self: self._name)
    row = property(lambda self: self._row)

    # ...

    # ...

    # TODO : move these methods to Layer
    def move_behind(self, widget):

        self.layer.move_widget1_behind_widget2(widget1=self, widget2=widget)

    def move_in_front_of(self, widget):

        self.layer.move_widget1_in_front_of_widget2(widget1=self, widget2=widget)

    def swap_layer(self, layer):
        """ NOTE : cannot be called during construction """

        if isinstance(layer, str):
            layer = self.parent.layers_manager.get_layer(layer)
        self.parent.layers_manager.swap_layer(self, layer)
