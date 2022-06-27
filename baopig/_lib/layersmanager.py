
from .layer import Widget, Layer


class LayersManager:

    levels = {
        0:"BACKGROUND",
        1:"MAINGROUND",
        2:"FOREGROUND",
    }
    BACKGROUND = 0
    MAINGROUND = 1
    FOREGROUND = 2
    DEFAULT_LEVEL = MAINGROUND

    def __init__(self, container):

        self._container = container
        self._layers = []
        self._default_layer = None
        self._touchable_layers = []

    container = property(lambda self: self._container)
    default_layer = property(lambda self: self._default_layer)
    layers = property(lambda self: self._layers)
    touchable_layers = property(lambda self: self._touchable_layers)

    background = property(lambda self: self.get_level(self.BACKGROUND))
    foreground = property(lambda self: self.get_level(self.FOREGROUND))
    mainground = property(lambda self: self.get_level(self.MAINGROUND))

    def _add_layer(self, layer):
        """
        This method should only be called by Layer.__init__
        """

        assert len(layer) == 0, "A layer should be empty at its creation"
        assert layer.name not in self._layers
        assert layer.level in self.levels

        if layer.touchable:
            if self._default_layer is None:
                self._default_layer = layer

        self._layers.append(layer)
        self._sort_layers()
        self._touchable_layers = list(layer for layer in self._layers if layer.touchable)  # this preserv the overlay

    def _remove_layer(self, layer):
        """
        This method should only be called by Layer.kill
        """

        assert len(layer) == 0
        self._layers.remove(layer)
        if layer.touchable: self._touchable_layers.remove(layer)
        if layer == self.default_layer: self._default_layer = None

    def _sort_layers(self):

        layer_index = 0
        for level in sorted(self.levels.keys()):
            for layer in sorted(self.get_ilevel(level), key=lambda layer: layer.weight):
                layer._layer_index = layer_index
                layer_index += 1
        self._layers.sort(key=lambda layer: layer.layer_index)

    def accept(self, child):
        return isinstance(child, Widget)

    def add(self, child):
        """
        This method should only be called by Container.children._add
        You can override this function in order to define special behaviors
        """

        if self.default_layer is None:  # means there is no layer yet
            raise AssertionError
        if child.layer is None:
            raise AssertionError

        assert child.layer in self._layers, (child.layer, self.layers)

        child.layer.add(child)

    def get_ilevel(self, level):

        for layer in self._layers:
            if layer.level == level:
                yield layer

    def get_layer(self, layer_name):

        for layer in self._layers:
            if layer.name == layer_name:
                return layer  # if no layer is found, return None

    def get_level(self, level):

        return tuple(self.get_ilevel(level))

    def remove(self, child):

        assert child.layer in self._layers, child.layer
        child.layer.remove(child)

    def set_default_layer(self, layer):

        if isinstance(layer, str):
            layer = self.get_layer(layer)
        self._default_layer = layer

    def find_layer_for(self, child, layer_level=None):

        if layer_level is None: layer_level = self.DEFAULT_LEVEL

        for layer in self.layers:
            if layer.level == layer_level and layer.accept(child):
                return layer
        return Layer(self.container, level=layer_level, name="automaticlyCreatedLayer")

    def swap_layer(self, child, layer):

        assert layer in self._layers, layer
        if child.is_awake:
            assert child in child.layer, child.layer
            child.layer.remove(child)
            layer.add(child)
        child._layer = layer
        child.send_paint_request()
