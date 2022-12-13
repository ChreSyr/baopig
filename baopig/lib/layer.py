
from baopig.pybao.objectutilities import WeakTypedList
from .utilities import MarginType
from .widget import Widget, Communicative


class Layer(Communicative):
    """
    A Layer is a manager who contains some of its container's children.
    Every widget is stored in one of its parent's layers.
    The positions of widgets inside a layer define the overlay : first behind, last in front.
    Each layer can be overlaid in the foreground, the main ground or the background.
    2 layers from the same ground are overlaid depending on their weight : a weight of 0 means it needs
    to stand behind a layer with weight 6. The default weight is 2.
    """

    def __init__(self, container, *filter_cls, name=None, level=None, weight=None, padding=None, spacing=None,
                 default_sortkey=None, sort_by_pos=False, touchable=True, maxlen=None, adaptable=False):
        """
        :param container: the Container who owns the layer
        :param name: an unic identifier for the layer
        :param filter_cls: a class or list of class from wich every layer's widget must herit
        :param level: inside the container's layers : lowest behind greatest in front, default to MAINGROUND
        :param weight: inside the layer's level : lowest behind greatest in front, default to 2
        :param padding: space between the widgets and the container. If None, set to the container's padding
        :param spacing: space between 2 widgets. If None, set to the container's spacing
        :param default_sortkey: default key fo layer.sort(). if set, at each append, the layer will be sorted
        :param sort_by_pos: if set, the default sortkey will be a function who sort children by y then x
        :param touchable: children of non-touchable layer are not hoverable
        :param maxlen: the maximum numbers of children the layer can contain
        """  # TODO : start_pos

        if name is None:
            name = "UnnamedLayer{}".format(len(container.layers))
        if not filter_cls:
            filter_cls = [Widget]
        if level is None:
            level = container.layers_manager.DEFAULT_LEVEL
        if weight is None:
            weight = 2
        if padding is None:
            padding = container.padding  # Same object
        else:
            padding = MarginType(padding)
        if spacing is None:
            spacing = container.spacing  # Same object
        else:
            spacing = MarginType(spacing)
        if sort_by_pos:
            assert default_sortkey is None
            default_sortkey = lambda c: (c.rect.top, c.rect.left)

        for filter_class in filter_cls:
            assert issubclass(filter_class, Widget), filter_class
        assert isinstance(name, str), name
        assert name not in container.layers, name
        assert level in container.layers_manager.levels, level
        assert isinstance(weight, (int, float)), weight
        assert isinstance(padding, MarginType), padding
        assert isinstance(spacing, MarginType), spacing
        if default_sortkey is not None:
            assert callable(default_sortkey), default_sortkey
        if maxlen is not None:
            assert isinstance(maxlen, int), maxlen

        Communicative.__init__(self)

        # NOTE : adaptable, container, name, touchable and level are not editable, because you
        #        need to know what kind of layer you want since its creation
        self._is_adaptable = bool(adaptable)
        self._widgets = WeakTypedList(*filter_cls)
        self._container = container
        self._filter = filter_cls
        self._name = name
        self._level = level
        self._weight = weight
        self._padding = padding
        self._spacing = spacing
        self.default_sortkey = default_sortkey  # don't need protection
        self._layer_index = None  # defined by container.layers
        self._layers_manager = container.layers_manager
        self._maxlen = maxlen
        self._touchable = bool(touchable)

        self.layers_manager._add_layer(self)

    def __add__(self, other):
        return self._widgets + other

    def __bool__(self):
        return bool(self._widgets)

    def __contains__(self, item):
        return self._widgets.__contains__(item)

    def __getitem__(self, item):
        return self._widgets.__getitem__(item)

    def __iter__(self):
        return self._widgets.__iter__()

    def __len__(self):
        return self._widgets.__len__()

    def __repr__(self):
        return "{}(name:{}, index:{}, filter_cls:{}, touchable:{}, level:{}, weight:{}, children:{})".format(
            # "Widgets" if self.touchable else "",
            self.__class__.__name__, self.name, self._layer_index, self._filter, self.touchable,
            self.level, self.weight, self._widgets)

    spacing = property(lambda self: self._spacing)
    container = property(lambda self: self._container)
    is_adaptable = property(lambda self: self._is_adaptable)
    layer_index = property(lambda self: self._layer_index)
    layers_manager = property(lambda self: self._layers_manager)
    level = property(lambda self: self._level)
    maxlen = property(lambda self: self._maxlen)
    name = property(lambda self: self._name)
    padding = property(lambda self: self._padding)
    touchable = property(lambda self: self._touchable)
    weight = property(lambda self: self._weight)

    def accept(self, widget):

        if self.maxlen and self.maxlen <= len(self._widgets):
            return False
        return self._widgets.accept(widget)

    def add(self, widget):
        """
        WARNING : This method should only be called by the LayersManager: cont.layers_manager
        You can override this function in order to define special behaviors
        """
        if self.maxlen and self.maxlen <= len(self._widgets):
            raise PermissionError("The layer is full (maxlen:{})".format(self.maxlen))

        self._widgets.append(widget)
        if self.default_sortkey:
            self.sort()

        if self.is_adaptable:
            self.container.adapt(self)

    def clear(self):

        for widget in tuple(self._widgets):
            widget.kill()

    def get_visible_widgets(self):
        for widget in self._widgets:
            if widget.is_visible:
                yield widget

    visible = property(get_visible_widgets)

    def index(self, widget):
        return self._widgets.index(widget)

    def kill(self):

        self.clear()
        self.layers_manager._remove_layer(self)

    def move_at_bottom(self, widget):
        self.overlay(0, widget)

    def move_on_top(self, widget):
        self.overlay(len(self) - 1, widget)

    def move_widget1_behind_widget2(self, widget1, widget2):
        assert widget1 in self._widgets, f"{widget1} not in {self}"
        assert widget2 in self._widgets, f"{widget2} not in {self}"
        w1_index = self.index(widget1)
        w2_index = self.index(widget2)
        if w1_index < w2_index:
            if w1_index + 1 == w2_index:
                return
            w2_index -= 1
        self.overlay(w2_index, widget1)

    def move_widget1_in_front_of_widget2(self, widget1, widget2):
        assert widget1 in self, f"{widget1} not in {self}"
        assert widget2 in self, f"{widget2} not in {self}"
        w1_index = self.index(widget1)
        w2_index = self.index(widget2)
        if w1_index > w2_index:
            if w1_index - 1 == w2_index:
                return
            w2_index += 1
        self.overlay(w2_index + 1, widget1)

    def overlay(self, index, widget):
        """
        Move a widget at index
        """

        assert widget in self._widgets, f"{widget} not in {self}"
        self._widgets.remove(widget)
        self._widgets.insert(index, widget)
        self.container._warn_change(widget.hitbox)

    def pack(self, key=None, axis="vertical", spacing=None, padding=None, start_pos=(0, 0)):
        """
        Place children on one row or one column, sorted by key (default : pos)
        axis can either be horizontal or vertical
        NOTE : if motivated, can add 'sticky' param, which places the packed children from a corner or the center
        """
        if key is None:
            key = lambda o: (o.rect.top, o.rect.left)
        if spacing is None:
            spacing = self._spacing
        if padding is None:
            padding = self._padding
        if not isinstance(spacing, MarginType):
            spacing = MarginType(spacing)
        if not isinstance(padding, MarginType):
            padding = MarginType(padding)

        sorted_children = sorted(self, key=key)

        left, top = padding.left + start_pos[0], padding.top + start_pos[1]
        for widget in sorted_children:
            if widget.has_locked("pos"):
                raise PermissionError("Cannot pack a layer who contains locked children")
            widget.set_pos(topleft=(left, top))

            if axis == "horizontal":
                left = widget.hitbox.right + spacing.left
            elif axis == "vertical":
                top = widget.hitbox.bottom + spacing.top
            else:
                raise ValueError(f"axis must be either 'horizontal' or 'vertical', not {axis}")

    def remove(self, widget):
        """
        WARNING : This method should only be called by the LayersManager: cont.layers_manager
        You can override this function in order to define special behaviors
        """
        self._widgets.remove(widget)

        if self.is_adaptable:
            self.container.adapt(self)

    def set_filter(self, filter_cls):

        self._widgets.set_ItemsClass(filter_cls)

    def set_maxlen(self, maxlen):

        assert isinstance(maxlen, int) and len(self._widgets) <= maxlen
        self._maxlen = maxlen

    def set_weight(self, weight):

        assert isinstance(weight, (int, float))
        self._weight = weight
        self.layers_manager.sort_layers()

    def sort(self, key=None):
        """
        Permet de trier les enfants d'un layer selon une key
        Cette fonction ne deplace pas les enfants, elle ne fait que changer leur
        superpositionnement
        """
        if key is None:
            key = self.default_sortkey
        if key is None:  # No sort key defined
            return
        self._widgets.sort(key=key)
