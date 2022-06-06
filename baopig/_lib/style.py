
import inspect


class MemoryDict(dict):

    def __init__(self):

        self._modified_keys = set()

    def __repr__(self):
        string = "{"
        for key in self.all_keys():
            string += f"'{key}': {self[key]}, "
        string += "}"
        return string

    def __setitem__(self, key, value):

        super().__setitem__(key, value)
        self._modified_keys.add(key)

    def all_keys(self):
        return set(self.keys())

    def subdict(self):
        return SubMemoryDict(self)


class SubMemoryDict(MemoryDict):

    def __init__(self, superdict):

        assert isinstance(superdict, MemoryDict)
        self._superdict = superdict
        MemoryDict.__init__(self)

    def __contains__(self, key):

        for key2 in self.keys():
            if key2 == key:
                return True
        return key in self._superdict

    def __getitem__(self, key):

        for key2, value in dict.items(self):
            if key2 == key:
                return value
        return self._superdict[key]

    def all_keys(self):
        return self._superdict.all_keys().union(set(self.keys()))


class StyleClass:

    def __init__(self):

        self._dict = MemoryDict()
        self._types = MemoryDict()
        self._constraints = MemoryDict()
        self._constraint_error_messages = MemoryDict()
        self._theme = None
        self._priority = 0
        self._priority_dict = MemoryDict()

    def __contains__(self, key):
        return key in self._dict

    def __getitem__(self, key):
        try:
            return self._dict[key]
        except KeyError:
            raise KeyError(f"'{key}' is not a style attribute (attributes={self._dict.all_keys()})")

    def __repr__(self):
        return f"Style{self._dict}"

    def _setitem(self, key, value):
        self._dict[key] = value
        self._priority_dict[key] = self._priority
        self.check_type(key)
        self.check_constraint(key)

    def _apply_on_instanciatedstyle(self, style):

        # SuperButton -> Button -> Container
        #      |            |
        #     red         blue            <- default style
        #                   |
        #                yellow           <- style for a whole application
        #
        # A SuperButton has to be red, there is a priority

        assert isinstance(style, InstanciatedStyle)
        for attr in "_dict", "_types", "_constraints", "_constraint_error_messages":
            defined_keys = getattr(style, attr).all_keys()
            for key, value in getattr(self, attr).items():
                if key in defined_keys:  # this attribute is already defined by a substyle
                    if style.get_priority(key) >= self.get_priority(key):
                        continue
                getattr(style, attr)[key] = value

    def check_constraint(self, key):
        """Check if the value at key follows the defined constraint"""

        constraint = self.get_constraint(key)
        if constraint is None: return
        value = self[key]
        try:
            ok = constraint(value)
            if not ok: raise ValueError(f"Wrong value for {key} : {value}")
        except Exception as e:
            custom_message = self.get_constraint_error_message(key)
            if custom_message is not None:
                raise e.__class__(str(e) + ", " + custom_message)
            raise e

    def check_type(self, key):
        """Check if the value at key matches with defined type, but don't apply the type"""

        type = self.get_type(key)
        if type is None: return
        value = self[key]
        if isinstance(value, type): return
        if isinstance(value, str) and value.startswith("theme-"): return
        try:
            value = type(value)  # raise an error if this is impossible
        except Exception as e:
            raise e.__class__(str(e), f", value for {key} must be convertible in type {type}")

    def create(self, **kwargs):

        for key, value in kwargs.items():
            if key in self._dict:
                raise KeyError(f"This style attribute has already been created : {key}")
            self._setitem(key, value)

    def modify(self, **kwargs):
        """
        Works ike this :
        
        a_widget.style.modify(width=30)
        
        This will affect the appearance only if called before the Widget constructor
        """

        for key in self._dict.all_keys():
            if key in kwargs:
                self._setitem(key, kwargs.pop(key))

        if kwargs:
            raise KeyError(
                f"'{kwargs.keys()}' are not style attributes (attributes={self._dict.all_keys()})")

    def get_all_keys(self):
        """Return a set containing all style attributes"""
        return self._dict.all_keys()

    def get_constraint(self, key):

        try:                return self._constraints[key]
        except KeyError:    return None

    def get_constraint_error_message(self, key):

        try:                return self._constraint_error_messages[key]
        except KeyError:    return None

    def get_priority(self, key):

        return self._priority_dict[key]

    def get_type(self, key):

        try:                return self._types[key]
        except KeyError:    return None

    def get_modified_keys(self):
        """Return a generator containing all style attributes modified by this style, not its superstyle"""
        return self._dict.keys()

    def set_constraint(self, key, constraint, error_message=None):
        """
        bool(constraint(style[key])) must always return True
        If constraint is None, remove the current constraint
        WARNING : you can only set one constraint per key
        """

        if constraint is None:
            self._constraints[key] = lambda val: True  # prevent from getting super-style constraint
            if key in self.constraints_error_messages:
                self._constraints_error_messages.pop(key)
            return
        assert callable(constraint)
        assert len(inspect.signature(constraint).parameters) == 1, \
            "A constraint must only accept one parameter, the checked value"
        self._constraints[key] = constraint
        if error_message is not None:
            assert isinstance(error_message, str)
            self._constraint_error_messages[key] = error_message
        self.check_constraint(key)  # check constraint on current value

    def set_type(self, key, type):

        if type is None:
            self._types[key] = UndefinedType  # prevent from getting super-style constraint
            return
        assert inspect.isclass(type)
        self._types[key] = type
        self.check_type(key)

    def substyle(self):

        return SubStyleClass(self)


class SubStyleClass(StyleClass):

    def __init__(self, superstyle):

        assert isinstance(superstyle, StyleClass)

        self._super = superstyle
        self._dict = superstyle._dict.subdict()
        self._types = superstyle._types.subdict()
        self._constraints = superstyle._constraints.subdict()
        self._constraint_error_messages = superstyle._constraint_error_messages.subdict()
        self._theme = None
        self._priority = superstyle._priority + 1
        self._priority_dict = superstyle._priority_dict.subdict()


class InstanciatedStyle(SubStyleClass):
    """InstanciatedStyle has copied values, types, constraints and error messages

    It is needed in order to stop every inheritance from the theme style"""
    def __init__(self, owner):

        self._owner = owner
        SubStyleClass.__init__(self, owner.__class__.STYLE.substyle())
        theme = owner.theme
        self._theme = theme

        # classes : all the super classes of the owner for wich a special style is defined in theme
        classes = (super_class for super_class in theme.get_set_classes()
                   if issubclass(owner.__class__, super_class))
        classes = sorted(classes, key=lambda cls: -len(cls.mro()))

        for super_class in classes:
            superclass_style = theme.get_style_for(super_class)
            superclass_style._apply_on_instanciatedstyle(self)

        for key in self._dict.all_keys():
            value = self[key]
            if hasattr(value, "copy") and not inspect.isclass(value):
                value = value.copy()
            if isinstance(value, str):
                if value.startswith("theme-"):
                    value = self._theme.get_value(value)
                elif value.startswith("CALCUL "):
                    value = eval(value[7:], {"self": owner})
            type = self.get_type(key)
            if type is not None:
                self._types[key] = type
                if not isinstance(value, type):
                    value = type(value)
            constraint = self.get_constraint(key)
            if constraint is not None: self._constraints[key] = constraint
            message = self.get_constraint_error_message(key)
            if message is not None: self._constraint_error_messages[key] = message
            self._dict[key] = value

    def _setitem(self, key, value):

        if isinstance(value, str) and value.startswith("theme-"):
            value = self._theme.get_value(value)
        type = self.get_type(key)
        if type is not None:
            if not isinstance(value, type):
                value = type(value)
        self._dict[key] = value
        self._priority_dict[key] = self._priority
        self.check_constraint(key)

    def set_theme(self, theme):

        if isinstance(theme, str):
            theme = all_themes[theme]
        assert isinstance(theme, Theme)
        self._theme = theme


class ThemeColors:

    def __init__(self, **kwargs):

        self.border = (0, 0, 0)
        self.content = (0, 200, 200)
        self.font = (0, 0, 0)
        self.font_opposite = (255, 255, 255)
        self.scene_background = (170, 170, 170)
        self.dialog_background = (120, 120, 120)
        self.selection = (167, 213, 255)
        self.selection_rect = (107, 107, 205, 40)
        self.selection_rect_border = (107, 107, 205)

        for key in tuple(kwargs.keys()):
            if hasattr(self, key):
                setattr(self, key, kwargs.pop(key))
        if kwargs:
            raise KeyError(f"Wrong color keys : {kwargs.keys()}")

    def copy(self):

        return ThemeColors(**vars(self))


class Theme:
    """
    A theme is a dictionnary of style and other attributes

    If you change a theme's colors, it wont affect existing subthemes's colors
    """

    def __init__(self):
        self._all_styles = {}
        self.colors = ThemeColors()
        self.colors2 = [
            (200, 200, 200),
            (0, 50, 50),
            (85, 85, 85),
            (100, 100, 100),
            (0, 0, 0),
            (24, 0, 200),
            (57, 57, 155, 40),
            (57, 57, 155),
        ]

    def __repr__(self):
        string = "Theme("
        classes = self.get_set_classes()
        # print(classes)
        for widget_class in classes:
            style = self.get_style_for(widget_class)
            string += f"\n\t{widget_class.__name__}: {style}"
        if classes:
            string += "\n"
        string += ")"
        return string

    def update_from_colors(self):

        self.colors_dict = {
            "border": self.colors[0],
            "content": self.colors[1],
            "font": self.colors[0],
            "font_opposite": self.colors[4],
            "scene_background": self.colors[2],
            "dialog_background": self.colors[3],
            "selection": self.colors[5],
            "selection_rect": self.colors[6],
            "selection_rect_border": self.colors[7],
        }

    def get_style_for(self, widget_class):
        """
        Return the defined style for a widget class in this theme.
        If there is no defined style, return the default style.
        
        WARNING : do never modify the returned style ! The consequences are tricky
                  use set_style_for() instead
        """

        for widget_class2, widget_defined_substyle in self._all_styles.items():
            if widget_class is widget_class2:
                return widget_defined_substyle
        return widget_class.STYLE

    def get_set_classes(self):
        """Return a set containing all widget classes whose style is defined by this theme"""
        return set(self._all_styles.keys())

    def get_value(self, string):
        assert isinstance(string, str) and string.startswith("theme-")
        value = string[6:]
        if value.startswith("color-"):
            return getattr(self.colors, value[6:])
        else:
            raise ValueError(f"Unknown attribute for theme : {string}")

    def issubtheme(self, theme):
        return False

    def modify_colors(self, **kwargs):

        for key in self.colors_dict.keys():
            if key in kwargs:
                self.colors_dict[key] = kwargs.pop(key)

        if kwargs:
            raise KeyError(f"These are not color keys : {kwargs.keys()} (color keys={self.colors_dict.keys()})")

    def set_style_for(self, *widget_classes, **style):

        for widget_class in widget_classes:
            if widget_class not in self._all_styles:
                self._all_styles[widget_class] = widget_class.STYLE.substyle()
            self._all_styles[widget_class].modify(**style)

    def subtheme(self):
        return SubTheme(self)


class SubTheme(Theme):

    def __init__(self, supertheme):
        assert isinstance(supertheme, Theme)
        self._super = supertheme
        self._all_styles = {}
        self.colors = supertheme.colors.copy()

    def __getitem__(self, key):

        return self.get_style_for(key)

    def get_style_for(self, widget_class):
        """
        WARNING : do never modify the returned style ! The consequences are tricky
                  use set_style_for() instead
        """

        for widget_class2, widget_defined_substyle in self._all_styles.items():
            if widget_class is widget_class2:
                return widget_defined_substyle
        return self._super.get_style_for(widget_class)

    def get_set_classes(self):
        """Return a set containing all widget classes whose style is defined by this theme"""
        return set(self._all_styles.keys()).union(self._super.get_set_classes())

    def issubtheme(self, theme):
        return theme is self._super

    def set_style_for(self, *widget_classes, **style):

        for widget_class in widget_classes:
            if widget_class not in self._all_styles:
                self._all_styles[widget_class] = self._super.get_style_for(widget_class).substyle()
            self._all_styles[widget_class].modify(**style)


class DarkTheme(Theme):

    def __init__(self):

        super().__init__()
        self.colors.border = (200, 200, 200)
        self.colors.font = (200, 200, 200)
        self.colors.font_opposite = (0, 0, 0)
        self.colors.content = (0, 50, 50)
        self.colors.scene_background = (85, 85, 85)
        self.colors.dialog_background = (100, 100, 100)
        self.colors.selection = (24, 0, 200)
        self.colors.selection_rect = (57, 57, 155, 40)
        self.colors.selection_rect_border = (57, 57, 155)


all_themes = {
    "default": Theme(),
    "dark": DarkTheme(),
}


class HasStyle:
    """
    A style is a dictionnary containing appearance attributes and values
    It is first inherited from parents then modified by the instance

    STYLE is a class attribute. It is the default style for the object.
    In order to properly override style from super class, you should always
    define style attributes as so:

    class MyWidget(SuperWidget):
        STYLE = SuperWidget.STYLE.substyle()
        STYLE["color"] = (0, 255, 0)

    A theme is a dictionnary of style and other attributes

    WARNING : you cannot change a widget's theme or style after its creation
    """

    def __init__(self, theme):
        if hasattr(self, "_style"):  # previously called 'inherit_style()' for an anticipated style
            return
        if isinstance(theme, str):
            theme = all_themes[theme]

        self._theme = theme
        self._style = InstanciatedStyle(self)  # TODO : do not touch an InstanciatedStyle ?

    style = property(lambda self: self._style)
    theme = property(lambda self: self._theme)

    def get_style_for(self, widget_class):
        """
        WARNING : do never modify the returned style ! The consequences are tricky
                  use set_style_for() instead
        """

        if not hasattr(self, "_theme"):
            raise PermissionError("You must inherit style before using it")
        return self.theme.get_style_for(widget_class)

    def inherit_style(self, theme, options=None, **kwargs):
        """
        In dict options, if a key is a style attribute, remove the item from options and apply to self.style
        In dict kwargs, remove every items with value at None and apply other to self.style
        """
        if hasattr(theme, "_parent"):
            self._parent = theme
        if options and "theme" in options:  # here, theme is the parent widget
            assert not isinstance(theme, Theme)
            supertheme = theme.theme
            theme = options.pop("theme")
            assert isinstance(theme, Theme)
            if not theme.issubtheme(supertheme):
                raise PermissionError("Must be an parent sub-theme")
        elif isinstance(theme, str):
            theme = all_themes[theme]
        elif not isinstance(theme, Theme):  # theme can be the parent widget
            theme = theme.theme.subtheme()
        HasStyle.__init__(self, theme)

        if options:
            for key, val in tuple(options.items()):
                if (val is not None) and (key in self.STYLE):
                    kwargs[key] = options.pop(key)
        if kwargs:
            kwargs = dict(filter(lambda item: item[1] is not None, kwargs.items()))
            self.style.modify(**kwargs)

    def set_style_for(self, *widget_classes, **kwargs):
        """
        Exemple :
        app.set_style_for(bp.Button, height=40)
        app.set_style_for(bp.Rectangle, color="blue", width=40)
        """

        if not hasattr(self, "_theme"):
            raise PermissionError("You must inherit style before using it")
        self.theme.set_style_for(*widget_classes, **kwargs)