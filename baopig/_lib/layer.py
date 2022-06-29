
from baopig.pybao.objectutilities import WeakTypedList
from .utilities import MarginType
from .widget import Widget, Communicative


class Layer(Communicative):
    """
    A Layer is a manager who contains some of its container's children.
    Every component is stored in one of its parent's layers.
    The positions of components inside a layer define the overlay : first behind, last in front.
    Each layer can be overlaid in the foreground, the main ground or the background.
    2 layers from the same ground are overlaid depending on their weight : a weight of 0 means it needs
    to stand behind a layer with weight 6. The default weight is 2.
    """

    def __init__(self, container, *filter, name=None, level=None, weight=None, padding=None, children_margins=None,
                 default_sortkey=None, sort_by_pos=False, touchable=True, maxlen=None, adaptable=False):
        """
        :param container: the Container who owns the layer
        :param name: an unic identifier for the layer
        :param filter: a class or list of class from wich every layer's component must herit
        :param level: inside the container's layers : lowest behind greatest in front, default to MAINGROUND
        :param weight: inside the layer's level : lowest behind greatest in front, default to 2
        :param padding: space between the widgets and the container. If None, set to the container's padding
        :param children_margins: space between 2 widgets. If None, set to the container's children_margins
        :param default_sortkey: default key fo layer.sort(). if set, at each append, the layer will be sorted
        :param sort_by_pos: if set, the default sortkey will be a function who sort components by y then x
        :param touchable: components of non-touchable layer are not hoverable
        :param maxlen: the maximum numbers of components the layer can contain
        """  # TODO : start_pos

        if name is None: name = "UnnamedLayer{}".format(len(container.layers))
        if not filter: filter = [Widget]
        if level is None: level = container.layers_manager.DEFAULT_LEVEL
        if weight is None: weight = 2
        if padding is None: padding = container.padding  # Same object
        else: padding = MarginType(padding)
        if children_margins is None: children_margins = container.children_margins  # Same object
        else: children_margins = MarginType(children_margins)
        if sort_by_pos:
            assert default_sortkey is None
            default_sortkey = lambda c: (c.top, c.left)

        for filter_class in filter: assert issubclass(filter_class, Widget), filter_class
        assert isinstance(name, str), name
        assert name not in container.layers, name
        assert level in container.layers_manager.levels, level
        assert isinstance(weight, (int, float)), weight
        assert isinstance(padding, MarginType), padding
        assert isinstance(children_margins, MarginType), children_margins
        if default_sortkey is not None: assert callable(default_sortkey), default_sortkey
        if maxlen is not None: assert isinstance(maxlen, int), maxlen

        Communicative.__init__(self)

        # NOTE : adaptable, container, name, touchable and level are not editable, because you
        #        need to know what kind of layer you want since its creation
        self._is_adaptable = bool(adaptable)
        self._comps = WeakTypedList(*filter)
        self._container = container
        self._filter = filter
        self._name = name
        self._level = level
        self._weight = weight
        self._padding = padding
        self._children_margins = children_margins
        self.default_sortkey = default_sortkey  # don't need protection
        self._layer_index = None  # defined by container.layers
        self._layers_manager = container.layers_manager
        self._maxlen = maxlen
        self._touchable = bool(touchable)

        self.layers_manager._add_layer(self)

    def __add__(self, other):
        return self._comps + other

    def __bool__(self):
        return bool(self._comps)

    def __contains__(self, item):
        return self._comps.__contains__(item)

    def __getitem__(self, item):
        return self._comps.__getitem__(item)

    def __iter__(self):
        return self._comps.__iter__()

    def __len__(self):
        return self._comps.__len__()

    def __repr__(self):
        return "{}(name:{}, index:{}, filter:{}, touchable:{}, level:{}, weight:{}, components:{})".format(
            # "Widgets" if self.touchable else "",
            self.__class__.__name__, self.name, self._layer_index, self._filter, self.touchable,
            self.level, self.weight, self._comps)

    children_margins = property(lambda self: self._children_margins)
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

    def accept(self, comp):

        if self.maxlen and self.maxlen <= len(self._comps): return False
        return self._comps.accept(comp)

    def add(self, comp):
        """
        WARNING : This method should only be called by the LayersManager: cont.layers_manager
        You can override this function in order to define special behaviors
        """
        if self.maxlen and self.maxlen <= len(self._comps):
            raise PermissionError("The layer is full (maxlen:{})".format(self.maxlen))

        self._comps.append(comp)
        if self.default_sortkey:
            self.sort()

        if self.is_adaptable:
            self.container.adapt(self)

    def clear(self):

        for comp in tuple(self._comps):
            comp.kill()

    def _find_place_for(self, comp):

        assert self.accept(comp), f"{self} don't accept {comp}"
        return (0, 0)

    def get_visible_comps(self):
        for comp in self._comps:
            if comp.is_visible:
                yield comp
    visible = property(get_visible_comps)

    def index(self, comp):
        return self._comps.index(comp)

    def kill(self):

        self.clear()
        self.layers_manager._remove_layer(self)

    def move_comp1_behind_comp2(self, comp1, comp2):
        assert comp1 in self._comps, "{} not in {}".format(comp1, self)
        assert comp2 in self._comps, "{} not in {}".format(comp2, self)
        self.overlay(self.index(comp2), comp1)

    def move_comp1_in_front_of_comp2(self, comp1, comp2):
        assert comp1 in self, "{} not in {}".format(comp1, self)
        assert comp2 in self, "{} not in {}".format(comp2, self)
        self.overlay(self.index(comp2) + 1, comp1)
        # self._remove(comp1)
        # super().insert(self.index(comp2) + 1, comp1)
        # self._warn_change(comp1.hitbox)

    def overlay(self, index, comp):
        """
        Move a component at index
        """

        assert comp in self._comps
        self._comps.remove(comp)
        self._comps.insert(index, comp)
        self.container._warn_change(comp.hitbox)

    def pack(self, key=None, axis="vertical", children_margins=None, padding=None, start_pos=(0, 0)):
        """
        Place children on one row or one column, sorted by key (default : pos)
        axis can either be horizontal or vertical
        NOTE : if motivated, can add 'sticky' param, which places the packed children from a corner or the center
        """
        if key is None: key = lambda o: (o.top, o.left)
        if children_margins is None: children_margins = self._children_margins
        if padding is None: padding = self._padding
        if not isinstance(children_margins, MarginType): children_margins = MarginType(children_margins)
        if not isinstance(padding, MarginType): padding = MarginType(padding)

        sorted_children = sorted(self, key=key)

        left, top = padding.left + start_pos[0], padding.top + start_pos[1]
        if axis == "horizontal":
            for comp in sorted_children:
                if comp.has_locked.origin:
                    raise PermissionError("Cannot pack a layer who contains locked children")
                if comp.window is not None:
                    comp.topleft = (left - comp.window[0], top - comp.window[1])
                else:
                    comp.topleft = (left, top)
                left = comp.hitbox.right + children_margins.left
        elif axis == "vertical":
            for comp in sorted_children:
                if comp.has_locked.origin:
                    raise PermissionError("Cannot pack a layer who contains locked children")
                if comp.window is not None:
                    comp.topleft = (left - comp.window[0], top - comp.window[1])
                else:
                    comp.topleft = (left, top)
                top = comp.hitbox.bottom + children_margins.top
        else:
            raise ValueError(f"axis must be either 'horizontal' or 'vertical', not {axis}")

    def remove(self, comp):
        """
        WARNING : This method should only be called by the LayersManager: cont.layers_manager
        You can override this function in order to define special behaviors
        """
        self._comps.remove(comp)

        if self.is_adaptable:
            self.container.adapt(self)

    def set_filter(self, filter):

        self._comps.set_ItemsClass(filter)

    def set_maxlen(self, maxlen):

        assert isinstance(maxlen, int) and len(self._comps) <= maxlen
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
        if key is None: key = self.default_sortkey
        if key is None:  # No sort key defined
            return
        self._comps.sort(key=key)
