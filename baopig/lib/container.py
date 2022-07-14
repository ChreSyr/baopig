

from baopig.pybao.objectutilities import *
from baopig.documentation import Container as ContainerDoc
from .imagewidget import Image
from .layer import Layer
from .layersmanager import LayersManager
from .widget_supers import Paintable, ResizableWidget, Runable
from .utilities import *


class BoxRect(pygame.Rect):

    def __init__(self, rect, margin, out=False):

        if out:
            pygame.Rect.__init__(
                self,
                rect.left - margin.left,
                rect.top - margin.top,
                rect.width + margin.left + margin.right,
                rect.height + margin.top + margin.bottom
            )
        else:
            pygame.Rect.__init__(
                self,
                rect.left + margin.left,
                rect.top + margin.top,
                rect.width - margin.left - margin.right,
                rect.height - margin.top - margin.bottom
            )


class ChildrenManager:
    """
    Class for an ordered list of children

    Widgets are sort by overlay, you can access to children sorted by their
    position with children.orderedbypos

    For more efficiency, you can access all the Handler_SceneClose children of a Container
    with Container.children.handlers_sceneclose
    """

    def __init__(self, owner):

        assert isinstance(owner, Container)

        self._owner = owner
        self.all = set()  # accessible via Container.children
        self.containers = set()
        self.handlers_sceneclose = set()
        self.handlers_sceneopen = set()
        self.runables = set()
        self._lists = {
            Handler_SceneClose: self.handlers_sceneclose,
            Handler_SceneOpen: self.handlers_sceneopen,
            Container: self.containers,
            Runable: self.runables,
        }
        self._strong_refs = set()

    def add(self, child):
        """
        This method should only be called by the Widget constructor
        """

        assert child.parent == self._owner
        if child.is_asleep:
            raise PermissionError("A Container cannot contain asleep widgets")

        if child in self.all:
            raise PermissionError(f"{child} already in {self}")

        self.all.add(child)
        self._strong_refs.add(child)
        self._owner.layers_manager.add(child)
        for children_class, children_set in self._lists.items():
            if isinstance(child, children_class):
                children_set.add(child)
        if child.is_visible:
            self._owner._warn_change(child.hitbox)

    def remove(self, child):

        if child.is_asleep:
            raise PermissionError("A Container cannot contain asleep widgets")

        self.all.remove(child)
        self._owner.layers_manager.remove(child)
        for children_class, children_set in self._lists.items():
            if isinstance(child, children_class):
                children_set.remove(child)
        if child.is_visible:
            self._owner._warn_change(child.hitbox)


class Container(ContainerDoc, ResizableWidget):
    """
    Abstract class for widgets who need to contain other widgets

    We need the self.container_[action]() functions for recursivity between Container,
    because a container can contain a Handler_SceneOpen without being a Handler_SceneOpen himself

    WARNING : Try to do not override 'container_something' methods
    """

    STYLE = ResizableWidget.STYLE.substyle()
    STYLE.create(
        background_color=(0, 0, 0, 0),  # transparent by default
        background_image=None,
        border_color="theme-color-border",
        border_width=0,
        children_margins=0,
        padding=0,
    )
    STYLE.set_type("background_color", Color)
    STYLE.set_type("border_color", Color)
    STYLE.set_type("border_width", int)
    STYLE.set_type("children_margins", MarginType)
    STYLE.set_type("padding", MarginType)

    # NOTE : if width or height is defined in style, and a background_image is set,
    # the width and height values will be ignored

    def __init__(self, parent, **kwargs):

        if hasattr(self, "_weakref"):  # Container.__init__() has already been called
            return

        self._children_manager = ChildrenManager(self)  # needed in ResizableWidget.__init__
        self._rect_to_update = None

        ResizableWidget.__init__(self, parent, **kwargs)

        self._children_to_paint = WeakSet()  # a set cannot have two same occurences

        # LAYERS - Only layers can guarantie the overlay
        layersmanager_class = LayersManager
        if "layersmanager_class" in kwargs:
            layersmanager_class = kwargs.pop("layersmanager_class")
            assert issubclass(layersmanager_class, LayersManager)
        self.layers_manager = layersmanager_class(self)
        self.layers = self.layers_manager.layers

        # Box attributes
        self._children_margins = self.style["children_margins"]
        self._border_color = self.style["border_color"]
        self._border_width = self.style["border_width"]
        self._padding = self.style["padding"]
        self._content_rect = BoxRect(self.auto_rect, self.padding)

        # BACKGROUND
        self._background_color = self.style["background_color"]
        self.background_layer = None
        self._background_image_ref = lambda: None
        background_image = self.style["background_image"]
        if background_image is not None:
            self.set_background_image(background_image)

        # self._flip()  # TODO : remove flip_all at application launch, because a Zone created
        #                   during the app lifetime is not correctly printed

    children = property(lambda self: self._children_manager.all)
    background_color = property(lambda self: self._background_color)
    default_layer = property(lambda self: self.layers_manager.default_layer)

    # Box attributes
    children_margins = property(lambda self: self._children_margins)
    # -
    border_width = property(lambda self: self._border_width)
    padding = property(lambda self: self._padding)
    # -
    border_rect = property(lambda self: self.auto_rect)
    content_rect = property(lambda self: self._content_rect)
    # -
    background_image = property(lambda self: self._background_image_ref())
    border_color = property(lambda self: self._border_color)

    def _add_child(self, child):
        self._children_manager.add(child)

    def _container_close(self):

        for cont in self._children_manager.containers:
            cont._container_close()
        for child in tuple(self._children_manager.handlers_sceneclose):  # tuple prevent from in-loop killed widgets
            child.handle_scene_close()

    def _container_open(self):

        for cont in self._children_manager.containers:
            cont._container_open()
        for child in self._children_manager.handlers_sceneopen:
            child.handle_scene_open()

    def _container_paint(self):
        """ Executes paint requests """

        # TODO : solve :     for cont in self._children_manager.containers:
        #                RuntimeError: Set changed size during iteration
        for cont in self._children_manager.containers:
            cont._container_paint()

        if self._children_to_paint:
            for child in tuple(self._children_to_paint):
                if child.is_visible:
                    child.paint()
                    if child._dirty == 1:
                        child._dirty = 0
                        self._children_to_paint.remove(child)
                    # LOGGER.debug("Painting {} from container {}".format(child, self))

        rect = self._update_rect()
        if rect:
            self._warn_parent(rect)

    def _container_refresh(self, recursive=False, only_containers=True, with_update=True):

        if recursive:
            for child in self.children:
                if isinstance(child, Container):
                    child._container_refresh(recursive, only_containers, with_update=False)
                elif not only_containers:
                    if isinstance(child, Paintable):
                        child.paint()
        if with_update:
            self._flip()
        else:
            self._flip_without_update()

    def _container_run(self):

        for cont in self._children_manager.containers:
            cont._container_run()
        for child in self._children_manager.runables:
            if child.is_running:
                child.run()

    def _flip(self):
        """Update all the surface"""

        if self.is_hidden:
            return
        self._flip_without_update()
        self.send_display_request()

    def _flip_without_update(self):
        """Update all the surface, but don't prevent the parent"""

        with paint_lock:  # prevents self._rect_to_update changes during self._update_rect()
            self._rect_to_update = pygame.Rect(self.auto_rect)
            self._update_rect()

    def _remove_child(self, child):
        self._children_manager.remove(child)
        if child in self._children_to_paint:
            self._children_to_paint.remove(child)

    def _update_rect(self):
        """
        How to update a given portion of the application ?

        This method is the answer.
        This container will update by himself the portion to update, storing the result
        into its surface. Then, it asks its parent to update the same portion,
        and its parent will use this container surface.

        But how can a container update its surface ?

        The container create a surface (rect_background) at the rect size. This new surface
        is going to replace a portion of the container surface corresponding to the rect to
        update, once every child have been blited on it.


        surface :         --------- - - - -----------------------

                                        ^
                                        |

        rect_background :            -------
                                     :     :
                                     :     :
                                     :     :
        child3 :        -------------
                                     :     :
        child2 :                ------------- - - - -             <- The solid line is hitbox, the entire line is rect
                                     :     :
        child1 :                ------------------------------
                                     :     :
        background :        --------------------------------------  <- self.surface is filled with background_color
                                     :     :
                                     :     :
                                     :     :
        rect to update :             :-----:

        """

        if self._rect_to_update is None:
            return
        if self.is_hidden:
            return

        with paint_lock:
            rect, self._rect_to_update = self._rect_to_update, None
            self.surface.fill(self.background_color, rect=rect)
            if self._border_width:
                pygame.draw.rect(self.surface, self._border_color, (0, 0) + self.rect.size, self._border_width * 2 - 1)

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
                                    (collision.left - child.rect.left, collision.top - child.rect.top)
                                    + collision.size), collision.topleft
                                )
                        except pygame.error:
                            # can be raised from a child.surface who is a subsurface from self.surface
                            assert child.surface.get_parent() is self.surface
                            child._flip_without_update()  # overdraw child.hitbox

            return rect

    def _warn_change(self, rect):
        """Request updates at rects referenced by self"""

        rect = self.auto_hitbox.clip(rect)
        if rect.size == (0, 0):
            return
        if self._rect_to_update is None:
            self._rect_to_update = pygame.Rect(rect)  # from ProtectedHitbox to pygame.Rect
        else:
            self._rect_to_update.union_ip(rect)

    def _warn_parent(self, rect):
        """Request updates at rects referenced by self"""

        self.send_display_request(rect=(self.rect.left + rect[0], self.rect.top + rect[1]) + tuple(rect[2:]))

    def adapt(self, children_list=None, vertically=True, horizontally=True):
        """
        Resize in order to contain every widget in children_list
        Not supposed to move children_list
        """

        if children_list is None:
            children_list = self.children
        children = tuple(children_list)
        self.resize(
            (max(widget.hitbox.right for widget in children) + self.padding.right
             if children else self.padding.left + self.padding.right) if horizontally else self.rect.w,
            (max(widget.hitbox.bottom for widget in children) + self.padding.bottom
             if children else self.padding.top + self.padding.bottom) if vertically else self.rect.h
        )

    def handle_resize(self):

        if self.background_image is not None:
            self.background_image.resize(*self.rect.size)
        self._content_rect = BoxRect(self.auto_rect, self.padding)
        self._flip_without_update()

    def has_layer(self, layer_name):
        return layer_name in (layer.name for layer in self.layers)

    def kill(self):

        self.hide()
        for child in tuple(self.children):
            child.kill()
        super().kill()

    def pack(self, *args, adapt=False, **kwargs):
        for layer in self.layers:
            layer.pack(*args, **kwargs)
        if adapt:
            self.adapt(self.children)

    def set_background_color(self, *args, **kwargs):

        self._background_color = Color(*args, **kwargs)
        self._warn_change(self.auto_hitbox)  # TODO : test it

    def set_background_image(self, surf, background_adapt=True):
        """
        If background_adapt is True, the surf adapts to the zone's size
        Else, the zone's size adapts to the background_image
        """
        if surf is None:
            if self.background_image is not None:
                with paint_lock:
                    self.background_image.kill()
            return
        if background_adapt and surf.get_size() != self.rect.size:
            surf = pygame.transform.scale(surf, self.rect.size)
        if self.background_layer is None:
            self.background_layer = Layer(self, Image, name="background_layer", level=self.layers_manager.BACKGROUND)
        with paint_lock:
            if self.background_image is not None:
                self.background_image.kill()
                assert self.background_image is None
            self._background_image_ref = Image(self, surf, pos=(0, 0), layer=self.background_layer).get_weakref()
            if background_adapt is False:
                self.resize(*self.background_image.size)

    def set_window(self, *args, **kwargs):

        super().set_window(*args, **kwargs)
        self._rect_to_update = pygame.Rect(self.auto_rect)
