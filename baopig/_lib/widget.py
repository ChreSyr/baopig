
# TODO : replace sticky and pos_ref and pos_ref_location by flags ?


import inspect
import pygame
from baopig.pybao.issomething import *
from baopig.pybao.objectutilities import EditableTuple, Object, PackedFunctions, TypedSet
from baopig._debug import *
from baopig.io import LOGGER, mouse
from baopig.communicative import Communicative
from .utilities import paint_lock, functools
from .style import HasStyle, StyleClass, Theme


if debug_del:
    _is_alive = True
    import gc  # garbage collector


class MetaPaintLocker(type):
    def __call__(self, *args, **kwargs):
        with paint_lock:
            widget = super().__call__(*args, **kwargs)
            if widget.collidemouse():
                mouse.update_hovered_comp()
            return widget


class MetaUndefinedType(type):
    def __instancecheck__(self, instance):
        return True


class UndefinedType(metaclass=MetaUndefinedType):
    """This class is used for undefined style types, since isinstance(obj, UndefinedType) -> True"""
    def __init__(self):
        raise PermissionError("This class should never be instanciated")


class WeakRef:
    def __init__(self, comp):
        self._comp = comp

    def __call__(self):
        return self._comp


class _Origin:
    """
    An Origin is referenced by its parent
    When the parent moves, the component follows

    A Origin coordinate can be given in different ways:
        - x = 4         sets x to 4 pixels
        - x = '10%'     sets x to self.parent.width * 10 / 100 (automatically updated)

    WARNING : A component with a dynamic origin (pourcentage position) cannot be manually
              moved by any other way than redefining the origin
    """

    def __init__(self, owner):

        """
        asked_pos is the distance between reference at reference_location and owner at location
        """
        self._owner_ref = owner.get_weakref()
        self._asked_pos = owner.style["pos"]
        self._from_hitbox = owner.style["pos_from_ref_hitbox"]
        self._location = owner.style["pos_location"]
        try:
            self._has_adaptable_size = isinstance(self.owner.style["width"], str) or isinstance(self.owner.style["height"], str)
        except KeyError:
            self._has_adaptable_size = False
        # We need to initialize reference before config
        reference = owner.style["pos_ref"]
        if reference is None: reference = owner.parent
        self._reference_ref = reference.get_weakref()
        self.reference.signal.RESIZE.connect(self._weak_update_owner_pos, owner=self.owner)
        if self._has_adaptable_size:
            self.reference.signal.RESIZE.connect(self.owner._update_size, owner=self.owner)
        if self.reference != owner.parent:
            self.reference.signal.MOTION.connect(self._weak_update_owner_pos, owner=self.owner)
        self._reference_location = owner.style["pos_ref_location"]
        try:
            assert self._reference_location != "top"
        except AssertionError:
            raise AssertionError

    def __str__(self):
        return "Origin(asked_pos={}, location={}, reference={}, reference_location={}, from_hitbox={}, " \
               "is_locked={})".format(self.asked_pos, self.location, self.reference,
                         self.reference_location, self.from_hitbox, self.owner.has_locked.origin)

    asked_pos = property(lambda self: self._asked_pos)
    from_hitbox = property(lambda self: self._from_hitbox)
    is_locked = property(lambda self: self.owner.has_locked.origin)
    location = property(lambda self: self._location)
    owner = property(lambda self: self._owner_ref())
    reference = property(lambda self: self._reference_ref())
    reference_location = property(lambda self: self._reference_location)

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
        new_pos = self.pos
        old_pos = getattr(self.owner.rect, self.location)
        if new_pos == old_pos: return
        self.owner._move(dx=new_pos[0] - old_pos[0], dy=new_pos[1] - old_pos[1])

    @staticmethod
    def accept(coord):

        if isinstance(coord, str):
            if not coord.endswith('%'):
                return False
            try:
                int(coord[:-1])
                return True
                return 0 <= int(coord[:-1]) <= 100
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
            return False

    def config(self, pos=None, location=None, reference_comp=None, reference_location=None,
               from_hitbox=None, locked=None):

        old_pos = self.pos if self._asked_pos else None
        old_location = self.location

        if locked is False:
            self.owner.has_locked.origin = False

        if self.is_locked:
            raise PermissionError("This origin is locked")

        if location is not None:
            self._location = WidgetLocation(location)

        if reference_comp is not None:
            assert isinstance(reference_comp, Widget)
            self.reference.signal.MOTION.rem_command(self._weak_update_owner_pos)
            self.reference.signal.RESIZE.rem_command(self._weak_update_owner_pos)
            if self._has_adaptable_size:
                self.reference.signal.RESIZE.rem_command(self.owner._update_size)
            self._reference_ref = reference_comp.get_weakref()
            self.reference.signal.RESIZE.connect(self._weak_update_owner_pos, owner=self.owner)
            if self.reference != self.owner.parent:
                self.reference.signal.MOTION.connect(self._weak_update_owner_pos, owner=self.owner)
            if self._has_adaptable_size:
                self.reference.signal.RESIZE.connect(self.owner._update_size)

        if reference_location is not None:
            self._reference_location = WidgetLocation(reference_location)

        if from_hitbox is not None:
            self._from_hitbox = bool(from_hitbox)

        if pos is not None:
            assert _Origin.accept(pos), f"Wrong position value : {pos} (see documentation above)"
            self._asked_pos = pos

        self.owner.move_at(self.pos, self.location)

        if locked is True:
            self.owner.has_locked.origin = True

    def get_pos_relative_to_owner_parent(self):

        pos = []

        if self.from_hitbox:  # from the reference hitbox

            # Percentage translation of asked_pos
            for i, c in enumerate(self._asked_pos):

                if isinstance(c, str):
                    if debug_with_assert:
                        if not c.endswith('%'):
                            raise ValueError(f"Uncorrect coordinate : {c}")
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
                    if debug_with_assert:
                        if not c.endswith('%'):
                            raise ValueError(f"Uncorrect coordinate : {c}")
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

    def lock(self):

        self.owner.has_locked.origin = True

    def unlock(self):

        self.owner.has_locked.origin = False


class _Window(tuple):
    follow_movements = False


class WidgetLocation(str):

    ACCEPTED = ("topleft", "midtop", "topright",
                "midleft", "center", "midright",
                "bottomleft", "midbottom", "bottomright")

    def __new__(cls, location):

        if location == "left":
            location = "midleft"
        elif location == "top":
            location = "midtop"
        elif location == "right":
            location = "midright"
        elif location == "bottom":
            location = "midbottom"
        if location not in WidgetLocation.ACCEPTED:
            raise ValueError(f"Wrong value for location : '{location}', "
                             f"must be one of {WidgetLocation.ACCEPTED}")
        return str.__new__(cls, location)


class ProtectedHitbox(pygame.Rect):
    """
    A ProtectedHitbox cannot be resized or moved
    """

    def __init__(self, *args, **kwargs):
        pygame.Rect.__init__(self, *args, **kwargs)
        object.__setattr__(self, "_mask", None)
        object.__setattr__(self, "err", PermissionError("A ProtectedHitbox cannot change at all"))

    def __setattr__(self, *args):

        raise PermissionError

    pos = property(lambda self: tuple(self[:2]))
    lpos = property(lambda self: self[:2], doc="A list containing the rect topleft")

    def clamp_ip(self, Rect):

        raise self.err

    def colliderect(self, rect):
        # TODO : collidemask
        return super().colliderect(rect)

    def inflate_ip(self, x, y):

        raise self.err

    def move_ip(self, x, y):

        raise self.err

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

    def union_ip(self, Rect):

        raise self.err

    def unionall_ip(self, Rect_sequence):

        raise self.err


class HasProtectedHitbox:
    """
    The pos parameter is in fact the origin, who will often coincide with the topleft
    """

    def __init__(self):

        """
        rect is the surface hitbox, relative to the parent
        abs_rect is the rect relative to the application (also called 'abs')
        auto_rect is the rect relative to the component itself -> topleft = (0, 0) (also called 'auto')
        window is the rect inside wich the surface can be seen, relative to the parent
        hitbox is the result of clipping rect and window.
        If window is set to None, the hitbox will equal to the rect
        abs_hitbox is the hitbox relative to the application
        auto_hitbox is the hitbox relative to the component itself
        """

        size = self.surface.get_size()
        self._rect = ProtectedHitbox((0, 0), size)
        self._abs_rect = ProtectedHitbox((0, 0), size)
        self._auto_rect = ProtectedHitbox((0, 0), size)
        self._window = None
        self._hitbox = ProtectedHitbox((0, 0), size)
        self._abs_hitbox = ProtectedHitbox((0, 0), size)
        self._auto_hitbox = ProtectedHitbox((0, 0), size)

        """
        MOTION is emitted when the absolute position of the component.rect moves
        It sends two parameters : dx and dy
        WARNING : the dx and dy are the motion of the component.rect ! This means, when the
                  component's parent moves, a MOTION.emit(dx=0, dy=0) is probalby raised.
                  In facts, if the component.origin.reference is not the parent, the motion
                  won't be dx=0, dy=0
        NOTE : an hitbox cannot move and be resized in the same time
        """
        self.create_signal("MOTION")
        self.create_signal("NEW_WINDOW")

        """
        A margin is a defined rectangle around the component's surface
        A margin have left, top, right and bottom attributes, they are the amount of
        space required between the hitbox sides and the surface
        The hitbox contain the margin, so it is occasionnaly bigger than surface
        """
        self._margin_TBR = Object(
            left=0,
            top=0,
            right=0,
            bottom=0,
        )

        """
        Change a surface via set_surface(...) is the only way to change a cmponent size
        Changing size will emit self.signal.RESIZE if the component is visible
        A component with locked size cannot be resized, but the surface can change
        
        When a component is resized, we need a point of reference (called origin) whose pixel
        will not move
        
        origin.location can be one of : topleft,      midtop,     topright,
                                        midleft,      center,     midright,
                                        bottomleft,   midbottom,  bottomright
        
        Exemple : origin.location = midright
                  if the new size is 10 more pixel on the width, then the origin is on the right,
                  so we add the 10 new pixels to the left 
        """
        self.create_signal("RESIZE")

        # This will initialize the rects and hiboxes
        self._origin = _Origin(owner=self)


        # self.move_at(self.origin.pos, self.origin.location)

        new = self.origin.pos
        old = getattr(self.rect, self.origin.location)
        # Rewrite a part of the move_at() method so we can skip this line
        # if old == new: return
        self._move(new[0] - old[0], new[1] - old[1])

        # print("NEW COMPONENT :", repr(self))

    # GETTERS ON PROTECTED FIELDS
    margin_TBR =            property(lambda self: self._margin)
    origin =            property(lambda self: self._origin)

    # HITBOX
    rect =              property(lambda self: self._rect)
    abs = abs_rect =    property(lambda self: self._abs_rect)
    auto = auto_rect =  property(lambda self: self._auto_rect)
    window =            property(lambda self: self._window)
    hitbox =            property(lambda self: self._hitbox)
    abs_hitbox =        property(lambda self: self._abs_hitbox)
    auto_hitbox =       property(lambda self: self._auto_hitbox)

    bottom =            property(lambda self: self._rect.bottom,        lambda self, v: self.move_at(v, "bottom"))
    bottomleft =        property(lambda self: self._rect.bottomleft,    lambda self, v: self.move_at(v, "bottomleft"))
    bottomright =       property(lambda self: self._rect.bottomright,   lambda self, v: self.move_at(v, "bottomright"))
    center =            property(lambda self: self._rect.center,        lambda self, v: self.move_at(v, "center"))
    centerx =           property(lambda self: self._rect.centerx,       lambda self, v: self.move_at(v, "centerx"))
    centery =           property(lambda self: self._rect.centery,       lambda self, v: self.move_at(v, "centery"))
    left =              property(lambda self: self._rect.left,          lambda self, v: self.move_at(v, "left"))
    midbottom =         property(lambda self: self._rect.midbottom,     lambda self, v: self.move_at(v, "midbottom"))
    midleft =           property(lambda self: self._rect.midleft,       lambda self, v: self.move_at(v, "midleft"))
    midright =          property(lambda self: self._rect.midright,      lambda self, v: self.move_at(v, "midright"))
    midtop =            property(lambda self: self._rect.midtop,        lambda self, v: self.move_at(v, "midtop"))
    pos = topleft =     property(lambda self: self._rect.topleft,       lambda self, v: self.move_at(v, "topleft"))
    right =             property(lambda self: self._rect.right,         lambda self, v: self.move_at(v, "right"))
    top =               property(lambda self: self._rect.top,           lambda self, v: self.move_at(v, "top"))
    topright =          property(lambda self: self._rect.topright,      lambda self, v: self.move_at(v, "topright"))
    x =                 property(lambda self: self._rect.x,             lambda self, v: self.move_at(v, "x"))
    y =                 property(lambda self: self._rect.y,             lambda self, v: self.move_at(v, "y"))

    h =                 property(lambda self: self._rect.h)
    height =            property(lambda self: self._rect.height)
    size =              property(lambda self: self._rect.size)
    w =                 property(lambda self: self._rect.w)
    width =             property(lambda self: self._rect.width)

    def _move(self, dx, dy):

        old_hitbox = tuple(self.hitbox)
        with paint_lock:

            pygame.Rect.__setattr__(self.rect, "left", self.rect.left+dx)
            pygame.Rect.__setattr__(self.rect, "top", self.rect.top+dy)
            pygame.Rect.__setattr__(self.abs_rect, "topleft", (self.parent.abs.left + self.left, self.parent.abs.top + self.top))

            if self.window is not None:

                if self.window.follow_movements:
                    self._window = _Window((self.window[0] + dx, self.window[1] + dy) + self.window[2:])
                    self.window.follow_movements = True
                    pygame.Rect.__setattr__(self.hitbox, "topleft", (self.hitbox.left+dx, self.hitbox.top+dy))
                    pygame.Rect.__setattr__(self.abs_hitbox, "topleft", (self.abs_hitbox.left+dx, self.abs_hitbox.top+dy))
                else:
                    self._hitbox = ProtectedHitbox(self.rect.clip(self.window))
                    pygame.Rect.__setattr__(self.abs_hitbox, "topleft", (self.parent.abs.left + self.hitbox.left, self.parent.abs.top + self.hitbox.top))
                    pygame.Rect.__setattr__(self.auto_hitbox, "topleft", (self.hitbox.left - self.rect.left, self.hitbox.top - self.rect.top))
                    if old_hitbox[2:] != self.hitbox.size:
                        pygame.Rect.__setattr__(self.abs_hitbox, "size", self.hitbox.size)
                        pygame.Rect.__setattr__(self.auto_hitbox, "size", self.hitbox.size)
            else:
                pygame.Rect.__setattr__(self.hitbox, "topleft", self.topleft)
                pygame.Rect.__setattr__(self.abs_hitbox, "topleft", self.abs.topleft)
                if debug_with_assert: assert self.auto_hitbox.topleft == (0, 0), self.auto_hitbox

            if debug_with_assert:
                try:
                    if self.window:
                        assert self.hitbox == self.rect.clip(self.window),\
                            "window={}, follow={}, rect={}, hitbox={}" \
                            "".format(self.window, self.window.follow_movements, self.rect, self.hitbox)
                    assert self.abs_hitbox.topleft == (self.parent.abs.left + self.hitbox.left, self.parent.abs.top + self.hitbox.top)
                    assert self.auto_hitbox.topleft == (self.hitbox.left - self.rect.left, self.hitbox.top - self.rect.top)
                except AssertionError as e:
                    raise e

            self.signal.MOTION.emit(dx, dy)

            # We reset the asked_pos after the MOTION in order to allow cycles of origin referecing
            if debug_with_assert: assert not self.has_locked.origin
            self.origin._reset_asked_pos()

            if self.is_visible:
                self.parent._warn_change(self.hitbox.union(old_hitbox))

    def _update_from_parent_movement(self):

        # Note : paint_lock is hold by the parent
        new_pos = self.origin.pos
        old_pos = getattr(self.rect, self.origin.location)
        if self.has_locked.origin:
            self.origin.unlock()
            self._move(dx=new_pos[0]-old_pos[0], dy=new_pos[1]-old_pos[1])
            self.origin.lock()
        else:
            self._move(dx=new_pos[0]-old_pos[0], dy=new_pos[1]-old_pos[1])

    def can_be_resized_at(self, size):

        if self.has_locked.width and size[0] != self.rect.w:
            return False
        if self.has_locked.height and size[1] != self.rect.h:
            return False

        return True

    def clamp_ip(self, Rect):

        raise PermissionError("not implemented")

    def inflate_ip(self, x, y):

        raise PermissionError("not implemented")

    def collidemouse(self):

        return self.abs_hitbox.collidepoint(mouse.pos)

    def lock_height(self, locked=True):
        self.has_locked.height = locked
        self.has_locked.size = self.has_locked.height and self.has_locked.width

    def lock_size(self, locked=True):
        self.has_locked.height = locked
        self.has_locked.width = locked
        self.has_locked.size = locked

    def lock_width(self, locked=True):
        self.has_locked.width = locked
        self.has_locked.size = self.has_locked.height and self.has_locked.width

    def move(self, dx=0, dy=0):

        if dx == 0 and dy == 0: return
        if self.has_locked.origin: return
        self._move(dx, dy)

    def move_at(self, value, key="topleft"):

        accepted = ("x", "y", "centerx", "centery", "top", "bottom", "left", "right", "topleft", "midtop", "topright", "midleft",
                       "center", "midright", "bottomleft", "midbottom", "bottomright")
        assert key in accepted, f"key '{key}' is not a valid rect position (one of {accepted})"

        if self.has_locked.origin:
            return

        old = getattr(self.rect, key)

        if old == value:
            return

        if isinstance(value, (int, float)):

            if key in ("x", "centerx", "left", "right"):
                self._move(value - old, 0)
            else:
                if debug_with_assert: assert key in ("y", "centery", "top", "bottom")
                self._move(0, value - old)

        else:
            self._move(value[0] - old[0], value[1] - old[1])

    def reference(self, pos):
        """
        Require a position relative to the application application
        Return the same position relative to the component's parent topleft
        """
        """if len(pos) == 4:
            rect = pos
            return self.reference((rect[0], rect[1])) + (rect[2], rect[3])"""

        return self.parent.abs_hitbox.referencing(pos)

    def set_window(self, window, follow_movements=None):
        """window is a rect relative to the parent

        follow_movements default to False"""

        if window is not None:
            if window == self.window: return
            assert is_typed_iterable(window, int, 4) or isinstance(window, pygame.Rect),\
                "Wrong recstyle object : {}".format(window)
            self._window = _Window(window)
            if follow_movements is not None:
                self._window.follow_movements = bool(follow_movements)

            old_pos = self.hitbox.topleft
            old_size = self.hitbox.size
            self._hitbox = ProtectedHitbox(self.rect.clip(self.window))
            pygame.Rect.__setattr__(self.abs_hitbox, "topleft", (self.parent.abs.left + self.hitbox.left, self.parent.abs.top + self.hitbox.top))
            # NOTE : should auto_hitbox.topleft be (0, 0) or the difference between self.pos and self.window.topleft ?
            pygame.Rect.__setattr__(self.auto_hitbox, "topleft", (self.hitbox.left - self.rect.left, self.hitbox.top - self.rect.top))
            pygame.Rect.__setattr__(self.abs_hitbox, "size", self.hitbox.size)
            pygame.Rect.__setattr__(self.auto_hitbox, "size", self.hitbox.size)

            if old_pos != self.hitbox.topleft:
                self.signal.MOTION.emit(self.left - old_pos[0], self.top - old_pos[1])
            if old_size != self.size:
                self.signal.RESIZE.emit(old_size)

            if debug_with_assert:
                assert self.abs_hitbox.left == self.parent.abs.left + self.hitbox.left
                assert self.abs_hitbox.top == self.parent.abs.top + self.hitbox.top
        else:
            self._window = None

        self.signal.NEW_WINDOW.emit()
        self.parent._warn_change(self.rect)  # rect is to cover all possibilities

        if debug_with_assert and window is not None:
            assert self.hitbox == self.rect.clip(self.window),\
                "window={}, rect={}, hitbox={}".format(self.window, self.rect, self.hitbox)

    # TODO : rework
    def config_margin(self, margin=None, left=None, top=None, right=None, bottom=None):

        if margin is not None:
            assert left is None
            assert top is None
            assert right is None
            assert bottom is None
            if hasattr(margin, "__iter__"):
                return self.set_margin(left=margin[0], top=margin[1], right=margin[2], bottom=margin[3])
            else:
                return self.set_margin(left=margin, top=margin, right=margin, bottom=margin)

        if left is not None: self.margin.left = left
        if top is not None: self.margin.top = top
        if right is not None: self.margin.right = right
        if bottom is not None: self.margin.bottom = bottom

    def update_pos(self):

        new_pos = self.origin.pos
        old_pos = getattr(self.rect, self.origin.location)
        if new_pos == old_pos: return
        self._move(dx=new_pos[0] - old_pos[0], dy=new_pos[1] - old_pos[1])


class HasProtectedSurface:

    def __init__(self, surface):

        assert isinstance(surface, pygame.Surface)

        """
        surface is the component's image

        Duing the component life, the size of surface can NOT differ from
        the size of the hitbox, it is protected thanks to this classe methods and ProtectedSurface
        
        NEW_SURF is emitted right after set_surface()
        """
        self._surface = surface
        self.create_signal("NEW_SURF")

    surface =            property(lambda self: self._surface)

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

        if self.has_locked.height and self.rect.height != surface.get_height():
            raise PermissionError("Wrong surface : {} (this component's surface height is locked at {})".format(surface, self.h))

        if self.has_locked.width and self.rect.width != surface.get_width():
            raise PermissionError("Wrong surface : {} (this component's surface width is locked at {})".format(surface, self.w))

        with paint_lock:
            if self.rect.size != surface.get_size():

                old_hitbox = tuple(self.hitbox)
                old_size = self.rect.size
                self._set_surface(surface)
                self.signal.RESIZE.emit(old_size)

                if self.is_visible:
                    self.parent._warn_change(self.hitbox.union(old_hitbox))

            else:

                self._surface = surface
                if self.is_visible:
                    self.parent._warn_change(self.hitbox)

            self.signal.NEW_SURF.emit()

    def subsurface(self, rect):
        """
        If a modification is set on a subsurface, this will change the parent surface,
        but this change won't be visible on screen.
        """

        return self.surface.subsurface(rect).copy()


class Widget(HasStyle, Communicative, HasProtectedSurface, HasProtectedHitbox,
             metaclass=MetaPaintLocker):
    """
    Abstract class for the elements of the screen
    A component can be visible, hidden, static, interactive, dynamic...
    Every component is child of one parent (baopig bio-logic, hmmm...)

    Every Widget have to make its surface at its creation
    """
    STYLE = StyleClass()
    STYLE.create(
        pos = (0, 0),
        pos_location = "topleft",
        pos_ref = None,  # default is parent
        pos_ref_location = "topleft",
        pos_from_ref_hitbox = False,
    )
    STYLE.set_type("pos_location", WidgetLocation)
    STYLE.set_type("pos_ref_location", WidgetLocation)

    def __init__(self, parent, surface, pos=None, origin=None, layer=None, name=None, row=None, col=None, **options):

        if name is None: name = "NoName"
        if isinstance(layer, str): layer = parent.layers_manager.get_layer(layer)

        assert hasattr(parent, "_warn_change")
        assert isinstance(name, str)

        """name is a string who may help to identify components"""
        # defined here so 'name' is first in self.__dict__
        self._name = name

        if "theme" in options:
            theme = options.pop("theme")
            assert isinstance(theme, Theme)
            if not theme.issubtheme(parent.theme):
                raise PermissionError("Must be an parent sub-theme")
        else:
            theme = parent.theme.subtheme()

        HasStyle.__init__(self, theme)

        if "style" in options:
            style = options.pop("style")
            if style:
                self.style.modify(**style)

        Communicative.__init__(self)
        HasProtectedSurface.__init__(self, surface)

        """parent is the Container who contains this Widget"""
        self._parent = parent

        """app is the Application who manages the scenes"""
        self._app = parent.app

        """a weakref will return None after widget.kill()"""
        self._weakref = WeakRef(self)

        """
        A visible component will be rendered on screen
        An invisible component will not be rendered
        
        At appearing, self.signal.SHOW is emitted
        At disappearing, self.signal.HIDE is emitted
        """
        self._is_visible = True
        if "visible" in options:
            self._is_visible = options.pop("visible")
        self.create_signal("SHOW")
        self.create_signal("HIDE")

        """
        dirty is True while the component's surface have not been updated
        
        Particularly usefull when a hidden component got updated
        We wait until it get visible before rendering it
        
        0 : don't need to be updated
        1 : need to be updated once
        2 : need to be updated as much as possible
        """
        self._dirty = 0

        """
        A sleeping component won't be visible and won't update itself until it awakes
        The memory is an object who remember all the changements the component should
        have done while it is sleeping
        When it awakes, it will operate all the changements
        
        Exemple : you can do
        
            comp.move_at((4, 4))
            comp.asleep()
            comp.move_at((10, 10))
            comp.wake()
            
            and the comp will reappear positionned at (10, 10)
        This is very usefull for components who are often hidden and shown
        """
        self._is_sleeping = False
        self._memory = Object(  # TODO : requests_at_awake
            need_appear=None,
            need_start_animation=None,
        )
        self.create_signal("ASLEEP")
        self.create_signal("WAKE")

        """A widget can have this attributes locked"""
        self._has_locked = Object(
            origin=False,
            width=False,
            height=False,
            size=False,
            visibility=False,
        )

        """
        A Widget have a lot of relations with other components, it is hard to remove
        all of them in order to delete the component
        
        Here's why listof_packedfunctions parameter :
        When a component own a method stored in a PackedFunction, if it don't directly
        own the PackedFunction, we need to remember that the component is the method
        owner and in wich PackedFunction that method is stored. This being done, we can
        remove the method from the PackedFunction in order to properly kill the component
        """
        self.create_signal("KILL")

        """
        The scene is always the same
        Since self is a scene's child, it doesn't need to only keep a weakref to it
        """
        self.__scene = parent.scene

        if pos:
            self.style.modify(pos=pos)
        self._col = None
        self._row = None
        if (col is not None) or (row is not None):
            """col and row attributes are destinated for GridLayer"""
            if (pos is not None) or \
                    ("pos_location" in options) or \
                    ("pos_ref" in options) or \
                    ("pos_ref_location" in options):
                raise PermissionError("When the layer manages the widget's position, "
                                      "all you can define is row, col and sticky")
            if col is None: col = 0
            if row is None: row = 0
            assert isinstance(col, int) and col >= 0
            assert isinstance(row, int) and row >= 0
            self._col = col
            self._row = row
        self._sticky = None
        if "sticky" in options:
            self._sticky = options.pop("sticky")
            self.style.modify(
                pos_location = self._sticky,
                pos_ref_location = self._sticky
            )
        if "pos_location" in options:
            self.style.modify(pos_location = options.pop("pos_location"))
        if "pos_ref" in options:
            self.style.modify(pos_ref = options.pop("pos_ref"))
        if "pos_ref_location" in options:
            self.style.modify(pos_ref_location = options.pop("pos_ref_location"))

        # TODO : center=(34, 45) instead of pos=(34, 45), pos_location="center"

        """
        A component is stored inside its parent, at one layer. A layer is identified
        via a string name. Default layer is defined by the parent. You can change a
        component layer via container.layer(component, layer_name) where layer_name
        references an existing layer.
        """
        layer_level = None
        if "layer_level" in options:
            assert layer is None, "Cannot define a layer AND a layer_level"
            layer_level = options.pop("layer_level")
        if layer is None:
            layer = parent.layers_manager.find_layer_for(self, layer_level)
        self._layer = layer
        # if col is not None:  # or col and row are at None, or they both are defined
        #     self.layer.

        # INITIALIZATIONS
        HasProtectedHitbox.__init__(self)
        self.parent._add_child(self)

        if debug_new:
            print("NEW COMPONENT :", self)

        if "touchable" in options:
            if options["touchable"] is False:
                self.set_nontouchable()
            options.pop("touchable")

        if options:
            raise ValueError(f"Unused options : {options}")

        def paint_decorator(widget, paint):
            functools.wraps(paint)
            def wrapped_func(*args, **kwargs):
                res = paint(*args, **kwargs)
                widget.parent._warn_change(widget.hitbox)
                return res
            return wrapped_func
        self.paint = paint_decorator(self, self.paint)

    def __del__(self):

        if debug_del:
            print("DELETE :", self)
            global _is_alive
            _is_alive = False

    def __repr__(self):
        """
        Called by repr(self)

        :return: str
        """
        # This complicated string creation is avoiding the o.__repr__()
        # in order to avoid representation of components
        return "<{}(name='{}', parent='{}', hitbox={})>".format(
            self.__class__.__name__, self.name, self.parent.name, self.hitbox
        )

    def __str__(self):
        """
        Called by str(self)
        """
        return f"{self.__class__.__name__}(name={self.name})"

    # GETTERS ON PROTECTED FIELDS
    app = application = property(lambda self: self._app)
    col =               property(lambda self: self._col)
    dirty =             property(lambda self: self._dirty)
    has_locked =        property(lambda self: self._has_locked)
    is_alive =          property(lambda self: self._weakref._comp is not None)
    is_awake =          property(lambda self: not self._is_sleeping)
    is_dead =           property(lambda self: self._weakref._comp is None)
    is_hidden =         property(lambda self: not self._is_visible)
    is_sleeping =       property(lambda self: self._is_sleeping)
    is_visible =        property(lambda self: self._is_visible)
    layer =             property(lambda self: self._layer)
    name =              property(lambda self: self._name)
    parent =            property(lambda self: self._parent)
    row =               property(lambda self: self._row)
    scene =             property(lambda self: self.__scene)
    sticky =            property(lambda self: self._sticky)

    def asleep(self):

        self.parent.asleep_child(self)

    def copy(self):
        """
        Abstract method
        """
        raise PermissionError("The copy() method has not been overriden")

    def depend_on(self, comp):

        self.connect("kill", comp.signal.KILL)

    def get_weakref(self, callback=None):
        """
        A weakref is a reference to an object
        callback is a function called when the component die

        Example :
            weak_ref = my_comp.get_weakref()
            my_comp2 = weak_ref()
            my_comp is my_comp2 -> return True
            del my_comp
            print(my_comp2) -> return None
        """
        if callback is not None:
            assert callable(callback)
            self.signal.KILL.connect(callback)
        return self._weakref

    def hide(self):
        """
        # NOTE : if overriden, be carefull -> you should call super().hide()
        """

        if self.has_locked.visibility: return

        if not self.is_visible:
            return

        if self.is_sleeping:
            self._memory.need_appear = False
            return

        self._is_visible = False

        if self == mouse.linked_comp:
            mouse._unlink()
        elif self.collidemouse():
            mouse.update_hovered_comp()

        self.parent._warn_change(self.hitbox)
        self.signal.HIDE.emit()

    def kill(self):

        if not self.is_alive: return
        with paint_lock:
            try:
                if debug_with_assert:
                    if self.is_awake:
                        assert self in self.parent.children
                    else:
                        assert self in self.parent.children.sleeping
                self.parent._remove_child(self)
                self.disconnect()
                self.signal.KILL.emit(self._weakref)
                self._weakref._comp = None
                if debug_with_assert: assert self not in self.parent.children
            except Exception as e:
                raise e

        if debug_kill:
            print("KILL :", self)

        if debug_del:
            global _is_alive
            _is_alive = True
            # import sys
            # warn_msg = "This component is not entirely deleted : {} (dependencies : {})"\
            #                    "".format(self, sys.getrefcount(self))
        del self
        if debug_del:
            if _is_alive:
                gc.collect()
                # if _is_alive:
                #     LOGGER.warning(warn_msg)
            _is_alive = True

    def lock_visibility(self, locked=True):

        if self.has_locked.visibility == locked: return
        self.has_locked.visibility = locked

    def move_behind(self, comp):

        if debug_with_assert: assert comp is not self
        self.layer.move_comp1_behind_comp2(comp1=self, comp2=comp)

    def move_in_front_of(self, comp):

        if debug_with_assert: assert comp is not self
        self.layer.move_comp1_in_front_of_comp2(comp1=self, comp2=comp)

    def paint(self):
        """
        This method is made for being overriden

        In your implementation, you can update the component's surface.
        If you use send_paint_request(), this method will be called when the next frame is rendered
        In fact, you can use paint() at any moment, but it is more efficient
        to update it through send_paint_request() if it is changing very often
        """
        pass

    def send_paint_request(self):

        if self._dirty == 0:
            self.parent._dirty_child(self, 1)

    def set_nontouchable(self):
        """Cannot go back"""

        # TODO : documentation
        # TODO : rework
        need_mouse_update = self.collidemouse()
        self.collidemouse = lambda: False
        if need_mouse_update: mouse.update_hovered_comp()

    def set_dirty(self, dirty):
        """
        Works as pygame.DirtySprite :

        if set to 1, it is repainted and then set to 0 again
        if set to 2 then it is always dirty (repainted each scene, flag is not reset)
        0 means that it is not dirty and therefor not repainted again
        """

        if debug_with_assert: assert dirty in (0, 1, 2)
        self.parent._dirty_child(self, dirty)

    def set_visibility(self, visible):

        if visible: self.show()
        else:       self.hide()

    def show(self):
        """
        If the component was awake and hidden, it will appear on the screen
        """

        if self.has_locked.visibility: return

        if self.is_visible:
            return

        if self.is_sleeping:
            self._memory.need_appear = True
            return

        self._is_visible = True

        if self.collidemouse():
            mouse.update_hovered_comp()
        self.parent._warn_change(self.hitbox)
        if self._dirty:
            self.send_paint_request()
        self.signal.SHOW.emit()

    def swap_layer(self, layer):

        if isinstance(layer, str): layer = self.parent.layers_manager.get_layer(layer)
        self.parent.layers_manager.swap_layer(self, layer)

    def toggle_sleeping(self):

        if self.is_sleeping:
            self.wake()
        else:
            self.asleep()

    def toggle_visibility(self):

        if self.is_visible:
            self.hide()
        else:
            self.show()

    @staticmethod
    def ivisibles_from(list):
        for comp in list:
            if comp.is_visible:
                yield comp

    def wake(self):

        self.parent.wake_child(self)

