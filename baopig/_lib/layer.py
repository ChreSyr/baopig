
from baopig.pybao.objectutilities import WeakTypedList
from .widget import Widget, Communicative


class Layer(Communicative):
    """
    A Layer is a manager who contains some of its container's children
    Every component is stored in one of its parent's layers
    The positions of components inside a layer define the overlay : first behind, last in front.
    Eache layer can be overlay in the foreground, the main ground or the background.
    Layers from one ground are overlay depending on their weight : a weight of 0 means it need
    to stand behind a layer with weight 6. The default weight is 2.
    """

    def __init__(self, container, *filter, name=None, level=None, weight=None,
                 default_sortkey=None, sort_by_pos=False, touchable=True, maxlen=None, adaptable=False):
        """
        :param container: the Container who owns the layer
        :param name: a unic identifier for the layer
        :param filter: a class or list of class from wich every layer's component must herit
        :param level: inside the container's layers : lowest behind greatest in front, default to MAINGROUND
        :param weight: inside the layer's level : lowest behind greatest in front, default to 2
        :param default_sortkey: default key fo layer.sort(). if set, at each append, the layer will be sorted
        :param sort_by_pos: if set, the default sortkey will be a function who sort components by y then x
        :param touchable: components of non touchable layer are not hoverable
        :param maxlen: the maximum numbers of components the layer can contain
        """

        if name is None: name = "UnnamedLayer{}".format(len(container.layers))
        if not filter: filter = [Widget]
        if weight is None: weight = 2
        if level is None: level = container.layers_manager.DEFAULT_LEVEL
        if sort_by_pos:
            assert default_sortkey is None
            default_sortkey = lambda c: (c.top, c.left)

        assert isinstance(name, str), name
        assert name not in container.layers, name
        for filter_class in filter: assert issubclass(filter_class, Widget), filter_class
        if default_sortkey is not None: assert callable(default_sortkey), default_sortkey
        if maxlen is not None: assert isinstance(maxlen, int), maxlen
        assert isinstance(weight, (int, float)), weight
        assert level in container.layers_manager.levels, level

        Communicative.__init__(self)

        # NOTE : adaptable, container, name, touchable and level are not editable, because you
        #        need to know what kind of layer you want since its creation
        self._is_adaptable = bool(adaptable)
        self._comps = WeakTypedList(*filter)
        self._container = container
        self._filter = filter
        self.default_sortkey = default_sortkey  # don't need protection
        self._layer_index = None  # defined by container.layers
        self._layers_manager = container.layers_manager
        self._maxlen = maxlen
        self._name = name
        self._touchable = bool(touchable)
        self._level = level
        self._weight = weight

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

    is_adaptable = property(lambda self: self._is_adaptable)
    container = property(lambda self: self._container)
    layer_index = property(lambda self: self._layer_index)
    layers_manager = property(lambda self: self._layers_manager)
    level = property(lambda self: self._level)
    maxlen = property(lambda self: self._maxlen)
    name = property(lambda self: self._name)
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

    def pack_TO_MOVE_OUT(self, key=None, horizontal=False, margin=None, padding=None, adapt=True):
        """
        Place children on one row or one column, sorted by key (default : pos)
        If horizontal is False, they will be placed vertically
        The margin is the space between two children
        The margin is the minimum space between a comp and the container's border
        If adapt is True, the container's sizes will try to adapt to the layer's
        children, including the padding
        """
        if key is None: key = lambda o: (o.top, o.left)
        if margin is None: margin = 0
        if padding is None: padding = 0

        sorted_children = sorted(self, key=key)

        if horizontal:
            left = padding
            for comp in self:
                comp.topleft = (left, padding)
                if comp.topleft != (left, padding):
                    raise PermissionError("Cannot pack a layer who contains locked children")
                left = comp.right + margin
        else:
            top = padding
            for comp in self:
                comp.topleft = (padding, top)
                if comp.topleft != (padding, top):
                    raise PermissionError("Cannot pack a layer who contains locked children")
                top = comp.bottom + margin

        if adapt:
            self.container.adapt(self, padding=padding)

    def remove(self, comp):
        """
        WARNING : This method should only be called by the LayersManager: cont.layers_manager
        You can override this function in order to define special behaviors
        """
        self._comps.remove(comp)

        if self.is_adaptable:  # TODO : test to adapt a Scene at (0, 0)
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
        self._comps.sort(key=key)


class TemporaryLayer(Layer):
    """
    A TemporaryLayer will kill itself when its last component is removed
    """

    def __init__(self, *args, **kwargs):

        Layer.__init__(self, *args, **kwargs)

    def remove(self, comp):

        super().remove(comp)
        if len(self._comps) is 0:
            for comp in self.container.children.sleeping:
                if comp.layer is self:
                    return
            self.kill()
