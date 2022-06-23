

from baopig.pybao.objectutilities import *
from baopig._debug import debug_screen_updates
from .utilities import *
from .widget import Widget
from .resizable import ResizableWidget
from .layersmanager import LayersManager


class Container(ResizableWidget):
    """
    Abstract class for widgets who need to contain other widgets

    We need the self.container_[action]() functions for recursivity between Container,
    because a container can contain an Handler_SceneOpen without being a Handler_SceneOpen himself

    WARNING : Try to do not override 'container_something' methods
    """

    STYLE = ResizableWidget.STYLE.substyle()
    STYLE.create(
        background_color = (0, 0, 0, 0),  # transparent by default
    )
    STYLE.set_type("background_color", Color)

    def __init__(self, parent, size=None, **options):
        """can be size=(50, 45) or width=50, height=45"""

        self.inherit_style(parent, options)

        if size is not None:
            self.style.modify(width=size[0], height=size[1])
        size = self.get_asked_size()

        class ChildrenList(set):
            """
            Class for an ordered list of children

            Widgets are sort by overlay, you can access to children sorted by their
            position with children.orderedbypos

            For more efficiency, you can access all the Handler_SceneClose children of a Container
            with Container.children.handlers_sceneclose
            """

            def __init__(children):
                set.__init__(children)

                children.asleep = set()
                children.awake = set()
                children.containers = set()
                children.handlers_sceneclose = set()
                children.handlers_sceneopen = set()
                children._lists = {
                    Handler_SceneClose: children.handlers_sceneclose,
                    Handler_SceneOpen: children.handlers_sceneopen,
                    Container: children.containers,
                }
                children._strong_refs = set()

            def _add(children, child):
                """
                This method should only be called by the Widget constructor
                """

                assert child.parent == self
                if child.is_asleep:
                    if child in children.asleep:
                        raise PermissionError(f"{child} already asleep in {children.asleep}")
                    children.asleep.add(child)
                    return

                if child in children.awake:
                    raise PermissionError(f"{child} already in {children}")

                children.awake.add(child)
                children._strong_refs.add(child)
                self.layers_manager.add(child)
                for children_class, children_set in children._lists.items():
                    if isinstance(child, children_class):
                        children_set.add(child)
                if child.is_visible:
                    self._warn_change(child.hitbox)

            def _remove(children, child):

                if child.is_asleep:
                    children.asleep.remove(child)
                else:
                    children.awake.remove(child)
                    self.layers_manager.remove(child)
                    for children_class, children_set in children._lists.items():
                        if isinstance(child, children_class):
                            children_set.remove(child)
                    if child.is_visible:
                        self._warn_change(child.hitbox)

            def add(children):
                raise PermissionError

            def remove(children):
                raise PermissionError
        self._children = ChildrenList()

        # Only layers can guarantie the overlay
        layersmanager_class = LayersManager
        if "layersmanager_class" in options:
            layersmanager_class = options.pop("layersmanager_class")
            assert issubclass(layersmanager_class, LayersManager)
        self.layers_manager = layersmanager_class(self)
        self.layers = self.layers_manager.layers

        self._children_to_paint = WeakTypedSet(Widget)  # a set cannot have two same occurences
        self._rects_to_update = None
        self._rect_to_update = None
        self._requests = PackedFunctions()  # using PackedFunctions allow to set an owner for a request

        # BACKGROUND
        background_color = self.style["background_color"]
        if background_color is None: background_color = (0, 0, 0, 0)
        self._background_color = Color(background_color)
        surf = pygame.Surface(size, pygame.SRCALPHA)

        ResizableWidget.__init__(self, parent, surface=surf, **options)

        if self.is_hidden:
            self.set_dirty(1)

    all_children = property(lambda self: self._children.awake.union(self._children.asleep))
    asleep_children = property(lambda self: self._children.asleep)
    awake_children = property(lambda self: self._children.awake)
    background_color = property(lambda self: self._background_color)
    default_layer = property(lambda self: self.layers_manager.default_layer)

    def _add_child(self, child):
        self._children._add(child)

    def _dirty_child(self, child, dirty):
        """
        Should only be called by Widget.send_paint_request()
        """
        try:
            assert (child in self._children.awake) or child is self  # for scenes
        except AssertionError as e:
            raise e
        assert dirty in (0, 1, 2)

        child._dirty = dirty
        if dirty:
            self._children_to_paint.add(child)
        elif child in self._children_to_paint:
            self._children_to_paint.remove(child)

    def _flip(self):
        """Update all the surface"""

        if self.is_hidden:  return
        self._flip_without_update()
        self.parent._warn_change(self.hitbox)

    def _flip_without_update(self):
        """Update all the surface, but don't prevent the parent"""

        if self.is_hidden:  return

        with paint_lock:
            # self._rects_to_update.clear()
            self._rect_to_update = None

            self.surface.fill(self.background_color)

            for layer in self.layers:
                for child in layer.visible:
                    try:
                        # collision is relative to self
                        collision = child.hitbox.clip(self.auto)
                        if collision == child.rect:
                            self.surface.blit(child.surface, child.rect.topleft)
                        else:
                            self.surface.blit(child.surface.subsurface(
                                (collision.left - child.rect.left, collision.top - child.rect.top) + collision.size),
                                collision.topleft
                            )
                    except pygame.error as e:
                        # can be raised from a child.surface who is a subsurface from self.surface
                        assert child.surface.get_parent() is self.surface
                        child._flip_without_update()  # overdraw child.hitbox

            if debug_screen_updates:
                LOGGER.info("update in {} :  {}".format(self, self.auto))

    def _find_place_for(self, child):

        if child.layer is None:
            self.layers_manager.set_layer_for(child)
        return child.layer._find_place_for(child)

    def _move(self, dx, dy):

        with paint_lock:
            super()._move(dx, dy)
            for tup in tuple(self.awake_children), tuple(self.asleep_children):
                for child in tup:
                    child._update_from_parent_movement()  # TODO : signal.MOTION ?

    def _remove_child(self, child):
        self._children._remove(child)

    def _update_rect(self):
        """
        How to update a given portion of the application ?

        This method is the answer.
        This container will update by himself the portion to update, storing the result
        into its surface. Then, it ask to its parent to update the same portion,
        and its parent will use this container surface.

        But how can a container update its surface ?

        The container create a surface (rect_background) at the rect size. This new surface
        is gonna replace a portion of the container surface corresponding to the rect to
        update, once every child have been blited on it.

        if all is set, will update all of the container's hitbox


        surface :         --------- - - - -----------------------

                                        ^
                                        |

        rect_background :            -------
                                     :     :
                                     :     :
                                     :     :
        child3 :        -------------
                                     :     :
        child2 :                ------------- - - - -             <- The solid line is hitbox, the dotted plus solid line is rect
                                     :     :
        child1 :                ------------------------------
                                     :     :
        background :        --------------------------------------  <- background is filled with background_color
                                     :     :
                                     :     :
                                     :     :
        rect to update :             :-----:

        """

        if self._rect_to_update is None: return
        if self.is_hidden:  return

        with paint_lock:
            # rects_to_update = tuple(self._rects_to_update)
            rect = self._rect_to_update
            self._rect_to_update = None
            # self._rects_to_update.clear()
            # for rect in rects_to_update:

            """
            Si, lorsqu'un un enfant change, un pixel passe de plein a transparent,
            il faut aller chercher la couleur de derriere
            C'est soit background_color, soit un autre enfant

            Si background_color a de la transparence, alors il ne suffit pas de faire un
            blit des enfants sur la surface definie par rect, il faut aussi la
            reinitialiser afin de ne pas superposer la transparence
            """
            self.surface.fill(self.background_color, rect)

            for layer in self.layers:
                for child in layer.visible:
                    if child.hitbox.colliderect(rect):

                        try:
                            # collision is relative to self
                            collision = child.hitbox.clip(rect)
                            if collision == child.rect:
                                self.surface.blit(child.surface, child.rect.topleft)
                            else:
                                self.surface.blit(child.surface.subsurface(
                                    (collision.left - child.rect.left, collision.top - child.rect.top) + collision.size),
                                    collision.topleft
                                )
                        except pygame.error as e:
                            # can be raised from a child.surface who is a subsurface from self.surface
                            assert child.surface.get_parent() is self.surface
                            child._flip_without_update()  # overdraw child.hitbox

            if debug_screen_updates:
                LOGGER.info("update in {} :  {}".format(self, rect))

            self._warn_parent(rect)

    def _warn_change(self, rect):
        """Request updates at rects referenced by self"""

        rect = self.auto_hitbox.clip(rect)
        if rect[2:] == (0, 0): return
        if self._rect_to_update is None:
            self._rect_to_update = pygame.Rect(rect)
        else:
            self._rect_to_update.union_ip(rect)  # TODO : with paint_lock
        # self._rects_to_update.add(rect)

    def _warn_parent(self, rect):
        """Request updates at rects referenced by self"""

        self.parent._warn_change(
            (self.rect.left + rect[0], self.rect.top + rect[1]) + tuple(rect[2:])
        )

    def adapt(self, children, padding=0, vertically=True, horizontally=True):
        """
        Resize in order to contain every widget in children
        Only use padding.right and padding.bottom, because it is not supposed to move children
        """

        list = tuple(children)
        padding = MarginType(padding)
        self.resize(
            (max(comp.right for comp in list)+padding.right
             if list else padding.right) if horizontally else self.w,
            (max(comp.bottom for comp in list)+padding.bottom
             if list else padding.bottom) if vertically else self.h
        )

    def asleep_child(self, child):

        if child.is_asleep:
            return

        assert child in self._children.awake

        child._memory.need_appear = child.is_visible
        # self.children.asleep.add(child)
        self._children._remove(child)
        child.hide()
        child._is_asleep = True
        self._children._add(child)
        child.signal.ASLEEP.emit()

    def container_close(self):  # TODO : private

        for cont in self._children.containers:
            cont.container_close()
        for child in tuple(self._children.handlers_sceneclose):  # tuple prevent from in-loop killed handlers_sceneclose
            child.handle_scene_close()

    def container_open(self):

        for cont in self._children.containers:
            cont.container_open()
        for child in self._children.handlers_sceneopen:
            child.handle_scene_open()

    def container_paint(self):

        for cont in self._children.containers:
            cont.container_paint()

        if self._children_to_paint:
            for child in tuple(self._children_to_paint):
                if child.is_visible:
                    child.paint()
                    if child._dirty == 1:
                        child._dirty = 0
                        self._children_to_paint.remove(child)
                    # LOGGER.debug("Painting {} from container {}".format(child, self))

        if self.dirty == 0:  # else, paint() is called by parent
            self._update_rect()

    def container_exec_requests(self):  # TODO

        self._requests()
        self._requests.clear()

    def fit(self, layer):

        assert layer in self.layers
        self.resize(max(c.right for c in layer), max(c.bottom for c in layer))

    def has_layer(self, layer_name):
        return layer_name in (layer.name for layer in self.layers)

    def kill(self):

        self.hide()
        for child in tuple(self.all_children):
            child.kill()
        super().kill()

    def paint(self, recursive=False, only_containers=True, with_update=True):

        if recursive:
            for c in self._children.awake:
                if isinstance(c, Container):
                    c.paint(recursive, only_containers, with_update=False)
                elif not only_containers:
                    c.paint()
        if with_update:
            self._flip()
        else:
            self._flip_without_update()

    def resize(self, w, h):

        if self.has_locked.width: w = self.w
        if self.has_locked.height: h = self.h
        if (w, h) == self.size: return

        need_alpha = pygame.SRCALPHA if self.background_color.has_transparency() else 0
        with paint_lock:
            super().set_surface(pygame.Surface((w, h), need_alpha))
            self._flip_without_update()

    def send_request(self, request, owner=None):

        assert callable(request)
        self._requests.add(request, owner=None)

    def set_always_dirty(self):
        """Lock self.dirty to 2, cannot go back"""

        self.set_dirty(2)
        self.set_dirty = lambda dirty: None
        self._warn_change = lambda rect: None
        # WARNING : this function is dirty...

    def set_background_color(self, *args, **kwargs):

        self._background_color = Color(*args, **kwargs)
        self.send_paint_request()

    def set_surface(self, surface):

        raise PermissionError("A Container manage its surface itself (it is the addition of its child surfaces)")

    def wake_child(self, child):

        if child.is_awake:
            return

        assert child in self._children.asleep

        self._children._remove(child)  # TODO : .remove & .add since ._children is no longer accessible
        child._is_asleep = False
        self._children._add(child)

        if child._memory.need_start_animation:
            child.start_animation()

        if child._memory.need_appear:
            child.show()

        child.send_paint_request()

        child._memory.need_appear = None
        child._memory.need_start_animation = None

        child.signal.WAKE.emit()

