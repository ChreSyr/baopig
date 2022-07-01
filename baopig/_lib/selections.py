import pygame
from baopig.pybao.issomething import is_point
from baopig.io import keyboard
from .utilities import Linkable, paint_lock
from .layer import Layer
from .widget import Widget
from .shapes import Rectangle
from .container import Container


class SelectableWidget(Widget):
    """
    A SelectableWidget is a Widget who can be selected

    You are selecting a SelectableWidget when :
        - You click on its selector (a parent), and then move the mouse while it is clicked, and
          the rect representing the drag collide with the SelectableWidget
        - You pressed Ctrl+A while its selector is focused

    The selection_rect closes when :
        - A mouse.LEFTCLICK occurs (not double clicks, wheel clicks...)
        - The SelectableWidget size or position changes

    You can rewrite the check_select(abs_rect) method for accurate selections (like SelectableText)
    You can rewrite the select() and unselect() methods for specific behaviors (like SelectableText)

    The get_selected_data() method return, when the SelectableWidget is selected, the SelectableWidget itself
    You will probably want to override this method
    """

    def __init__(self, parent, **kwargs):

        Widget.__init__(self, parent, **kwargs)

        self._is_selected = False

        selector = self.parent  # TODO self & remove 3 lines in TextEdit.__init__
        while not isinstance(selector, Selector):
            selector = selector.parent
        self._selector_ref = selector.get_weakref()

        assert self not in self.selector.selectables
        self.selector.selectables.add(self)

        self.signal.NEW_SURF.connect(self.handle_unselect, owner=self)
        self.signal.MOTION.connect(self.handle_unselect, owner=self)
        self.signal.HIDE.connect(self.handle_unselect, owner=self)
        self.signal.KILL.connect(lambda: self.selector.selectables.remove(self), owner=self)

    is_selected = property(lambda self: self._is_selected)
    selector = property(lambda self: self._selector_ref())

    def check_select(self, selection_rect):
        """
        Method called by the selector each time the selection_rect rect changes
        The selection_rect has 3 attributes:
            - start
            - end
            - rect (the surface between start and end)
        These attributes are absolute referenced, wich means they are relative
        to the application. Start and end attributes reffer to the start and end
        of the selection_rect, who will often be caused by a mouse link motion
        """

        assert self.is_alive
        if self.abs_hitbox.colliderect(selection_rect.abs_hitbox):
            self._is_selected = True
            self.handle_select()
        else:
            if not self.is_selected:
                return
            self._is_selected = False
            self.handle_unselect()

    def get_selected_data(self):

        if self.is_selected:
            return self

    def handle_select(self):
        """
        Called each time the selection rect move and collide with this SelectableWidget
        """

    def handle_unselect(self):
        """
        Called when the selection rect don't collide anymore with this SelectableWidget
        """


class DefaultSelectionRect(Rectangle):
    """
    A SelectionRect is a rect relative to the application
    """

    STYLE = Rectangle.STYLE.substyle()
    STYLE.modify(
        color="theme-color-selection_rect",
        border_color="theme-color-selection_rect_border",
        border_width=1,
    )

    def __init__(self, parent, start, end):
        Rectangle.__init__(
            self,
            parent=parent,
            pos=(0, 0),
            size=(0, 0),
            layer=parent.selectionrect_layer,
            name=parent.name + ".selection_rect"
        )
        self.start = None
        self.end = None
        self.parent._selection_rect_ref = self.get_weakref()
        self.set_visibility(parent._selectionrect_visibility)
        self.parent.signal.UNLINK.connect(self.hide, owner=self)

        self.set_start(start)
        self.set_end(end)

    def set_end(self, abs_pos):
        assert self.start is not None
        assert is_point(abs_pos)
        self.end = abs_pos
        rect = pygame.Rect(self.start,
                           (self.end[0] - self.start[0],
                            self.end[1] - self.start[1]))
        rect.normalize()
        self.move_at(self.reference(rect.topleft))
        self.resize(rect.w + 1, rect.h + 1)  # the selection_rect rect collide with mouse.pos
        self.clip(self.parent.auto_hitbox)

    def set_start(self, abs_pos):
        assert self.end is None
        assert is_point(abs_pos)
        self.start = abs_pos


class Selector(Linkable):
    """
    Abstract class for components who need to handle when they are linked
    and then, while the mouse is still pressed, to handle the mouse drag in
    order to simulate a rect from the link origin to the link position and
    select every SelectableWidget object who collide with this rect
    """

    def __init__(self, SelectionRectClass=None):

        if SelectionRectClass is None: SelectionRectClass = DefaultSelectionRect

        Linkable.__init__(self)

        assert issubclass(SelectionRectClass, DefaultSelectionRect)
        assert isinstance(self, Container)

        self.selectables = set()
        self._can_select = True
        self._selection_rect_ref = lambda: None
        self._selection_rect_class = SelectionRectClass
        self._selectionrect_visibility = True
        self.selectionrect_layer = None

        self.signal.DEFOCUS.connect(self.close_selection, owner=self)

    def _get_iselected(self):
        for comp in self.selectables:
            if comp.is_selected:
                yield comp

    _iselected = property(_get_iselected)
    is_selecting = property(lambda self: self._selection_rect_ref() is not None)
    selection_rect = property(lambda self: self._selection_rect_ref())

    def del_selection_data(self):
        """This method is called when the user press Ctrl + X"""

    def close_selection(self):

        if not self.is_selecting: return
        self.selection_rect.kill()
        for selectable in self._iselected:
            if not selectable.is_selected: continue
            selectable._is_selected = False
            selectable.handle_unselect()

    def enable_selecting(self, can_select=True):
        """
        Define the ability to make selections in a Selector
        """

        if bool(can_select) == self._can_select: return
        self._can_select = bool(can_select)
        if can_select:
            self.selectionrect_layer = Layer(self, self._selection_rect_class, name="selectionrect_layer",
                                             level=self.layers_manager.FOREGROUND, maxlen=1, touchable=False)
        else:
            self.close_selection()
            if self.selectionrect_layer:
                self.selectionrect_layer.kill()
                self.selectionrect_layer = None

    def end_selection(self, abs_pos, visible=None):
        """
        :param abs_pos: An absolute position -> relative to the scene
        :param visible: If you want to change the visibility until the next end_selection
        """

        if not self._can_select: return
        assert self.selection_rect is not None
        if abs_pos == self.selection_rect.end: return
        if visible is not None:
            self.selection_rect.set_visibility(visible)
        else:
            self.selection_rect.set_visibility(self._selectionrect_visibility)
        self.selection_rect.set_end((abs_pos[0], abs_pos[1]))
        for selectable in self.selectables:
            selectable.check_select(self.selection_rect)

    def get_selection_data(self):

        if not self.is_selecting:
            return
        selected = tuple(self._iselected)
        if not selected:
            return  # happens when the selection_rect didn't select anything
        sorted_selected = sorted(selected, key=lambda o: (o.abs.top, o.abs.left))
        return '\n'.join(str(s.get_selected_data()) for s in sorted_selected)

    def handle_keydown(self, key):

        super().handle_keydown(key)  # TAB and arrows management

        if keyboard.mod.ctrl:

            if key == pygame.K_a:  # Ctrl + a -> select all
                self.select_all()

            elif key == pygame.K_c:  # Cmd + c -> copy selected data
                selected_data = self.get_selection_data()
                if selected_data:
                    pygame.scrap.put(pygame.SCRAP_TEXT, str.encode(selected_data))

            elif key == pygame.K_v:  # Cmd + v -> paste clipboard data
                bytes = pygame.scrap.get(pygame.SCRAP_TEXT)
                if bytes is not None:
                    text = bytes.decode()
                    text = str.replace(text, '\0', '')  # removes null characters
                    text = str.replace(text, '\r', '')  # removes carriage return characters
                    self.paste(text)

            elif key == pygame.K_x:  # Cmd + x -> copy and cut selected data
                selected_data = self.get_selection_data()
                if selected_data:
                    pygame.scrap.put(pygame.SCRAP_TEXT, str.encode(selected_data))
                    self.del_selection_data()

    def handle_link(self):

        self.close_selection()  # only usefull at link while already focused
        for s in self.selectables:
            if hasattr(s, "handle_selector_link"):
                s.handle_selector_link()  # double & triple clicks on text

    def handle_link_motion(self, link_motion_event):
        with paint_lock:
            if self.selection_rect is None:
                self.start_selection(link_motion_event.origin)
            self.end_selection(link_motion_event.pos)

    def paste(self, data):
        """This method is called when the user press Ctrl + V"""

    def select_all(self):  # TODO : solve : selects also hidden selectables

        if self.selectables:
            if self.is_selecting:
                self.close_selection()
            self.start_selection(self.abs.topleft)
            self.end_selection(self.abs.bottomright, visible=False)

    def set_selectionrect_visibility(self, visible):

        self._selectionrect_visibility = bool(visible)
        if self.selection_rect is not None:
            self.selection_rect.set_visibility(visible)

    def start_selection(self, abs_pos):
        """
        A selection_rect can only be started once
        :param abs_pos: An absolute position -> relative to the scene
        """
        if not self._can_select: return
        if self.selection_rect is not None:
            raise PermissionError("A selection must be closed before creating a new one")
        self._selection_rect_class(self, abs_pos, abs_pos)
