

from .widget import Widget


class ResizableWidget(Widget):
    """
    Class for widgets who can be resized

    resize() method must be implemented
    """

    STYLE = Widget.STYLE.substyle()
    STYLE.create(
        width = None,  # must be filled
        height = None,  # must be filled
    )

    def _update_size(self):

        self.resize(*self.get_asked_size())

    def get_asked_size(self):

        size = (self.style["width"], self.style["height"])
        with_percentage = False
        for coord in size:
            if isinstance(coord, str):
                # hard stuff
                assert coord[-1] == '%'
                with_percentage = True
            else:
                assert isinstance(coord, (int, float)), f"Wrong value in size : {coord} (must be a number)"
                assert coord >= 0, f"Wrong value in size : {coord} (must be positive)"

        if with_percentage:
            size = list(size)
            for i, coord in enumerate(size):
                if isinstance(coord, str):
                    size[i] = self.parent.size[i] * int(coord[:-1]) / 100

                    # self.origin.reference.signal.RESIZE.connect(hardcoder)
                    # TODO WARNING : if the origin's reference gets changed, this is not updated

        return size

    def inherit_style(self, theme, options=None, **kwargs):

        size = None
        if options and "size" in options: size = options.pop("size")
        if "size" in kwargs: size = kwargs.pop("size")

        super().inherit_style(theme, options, **kwargs)

        if size is not None:
            self.style._setitem("width", size[0])
            self.style._setitem("height", size[1])

    def resize(self, w, h):
        """
        Here you set up your new component's surface
        """

    def resize_height(self, h):

        if h < 0: h = 0
        if h == self.h: return
        self.style.modify(height=h)
        self.resize(self.w, h)

    def resize_width(self, w):

        if w < 0: w = 0
        if w == self.w: return
        self.style.modify(width=w)
        self.resize(w, self.h)

    h =                 property(lambda self: self._rect.h, resize_height)
    height =            property(lambda self: self._rect.height, resize_height)
    size =              property(lambda self: self._rect.size, resize)
    w =                 property(lambda self: self._rect.w, resize_width)
    width =             property(lambda self: self._rect.width, resize_width)