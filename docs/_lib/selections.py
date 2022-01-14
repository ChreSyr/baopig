

import pygame
from baopig.pybao.objectutilities import WeakTypedSet, PackedFunctions, PrefilledFunction
from baopig.pybao.issomething import is_point
from baopig.io import mouse, keyboard, clipboard
from .utilities import Linkable, Focusable, paint_lock
from .layer import Layer
from .shapes import Rectangle
from .container import Container


class Selectable():
    """
    A Selectable is a Widget who can be selected

    You are selecting a Selectable when :
        - You click on its selector (a parent), and then move the mouse while it is clicked, and
          the rect representing the drag collide with the Selectable
        - You pressed Ctrl+A while its selector is focused

    The selection_rect closes when :
        - A mouse.LEFTCLICK occurs (not double clicks, wheel clicks...)
        - The Selectable size or position changes

    The default reaction is to call handle_select() and handle_unselect()
    You can rewrite the check_select(abs_rect) method for accurate selections (like SelectableText)
    You can rewrite the select() and unselect() methods for specific behaviors (like SelectableText)

    The get_selected_data() method return, when the Selectable is selected, the Selectable itself
    You will probably want to override this method
    """

    def __init__(self):

        self._is_selected = False

        selector = self.parent
        while not isinstance(selector, Selector):
            selector = selector.parent
        self._selector_ref = selector.get_weakref()

        self.handle_select = PackedFunctions()
        self.handle_unselect = PackedFunctions()

        # self.handle_select.add(PrefilledFunction(print, "HANDLE SELECT :", self))
        # self.handle_unselect.add(PrefilledFunction(print, "HANDLE UNSELECT :", self))

        if hasattr(self.selector, "selectables"):  # selector might not have been initialized
            self.selector.selectables.add(self)

        self.connect("unselect", self.signal.NEW_SURF)
        self.connect("unselect", self.signal.MOTION)
        self.connect("unselect", self.signal.HIDE)

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

        assert self.get_weakref()._comp is not None
        if self.abs_hitbox.colliderect(selection_rect.abs_hitbox):
            if not self.is_selected: self.handle_select()  # TODO : if not used, remove it ?
            self._is_selected = True
            self.select()
        else:
            if not self.is_selected: return
            self._is_selected = False
            self.unselect()
            self.handle_unselect()

    def get_selected_data(self):

        if self.is_selected:
            return self

    # TODO : decorate
    def select(self):
        """
        Called each time the selection rect move and collide with this Selectable
        """

    def unselect(self):
        """
        Called when the selection rect don't collide anymore with this Selectable
        """


class DefaultSelectionRect(Rectangle):
    """
    A SelectionRect is a rect relative to the application
    """

    STYLE = Rectangle.STYLE.substyle()
    STYLE.modify(
        color = "theme-color-selection_rect",
        border_color = "theme-color-selection_rect_border",
        border_width = 1,
    )

    def __init__(self, parent, start, end):

        Rectangle.__init__(
            self,
            parent=parent,
            pos=(0, 0),
            size=(0, 0),
            layer=parent.selectionrect_layer,
            name=parent.name+".selection_rect"
        )
        self.start = None
        self.end = None
        self.parent._selection_rect_ref = self.get_weakref()
        self.set_visibility(parent._selectionrect_visibility)
        self.connect("hide", self.parent.signal.UNLINK)

        self.set_start(start)
        self.set_end(end)

    def set_end(self, abs_pos):
        assert self.start is not None
        assert is_point(abs_pos)
        self.end = abs_pos
        left = min((self.start[0], self.end[0]))
        top = min((self.start[1], self.end[1]))
        rect = pygame.Rect(self.start,
                           (self.end[0] - self.start[0],
                            self.end[1] - self.start[1]))
        rect.normalize()
        # rect = self.parent.abs_hitbox.clip(rect)
        self.move_at(self.reference(rect.topleft))
        self.resize(rect.w+1, rect.h+1)  # the selection_rect rect collide with mouse.pos
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
    select every Selectable object who collide with this rect
    """

    def __init__(self, SelectionRectClass=None):

        # TODO : test : a disabled Selector cannot select

        if SelectionRectClass is None: SelectionRectClass = DefaultSelectionRect

        assert isinstance(self, Container)
        assert issubclass(SelectionRectClass, DefaultSelectionRect)
        Linkable.__init__(self)

        class Selectables(WeakTypedSet):
            def __init__(selectables):
                WeakTypedSet.__init__(selectables, ItemsClass=Selectable)
                def add_selectables(cont):
                    for comp in cont.children:
                        if hasattr(comp, "children"):
                            add_selectables(comp)
                        if isinstance(comp, Selectable):
                            selectables.add(comp)
                add_selectables(self)
            def add(selectables, comp):
                if comp not in selectables:
                    super().add(comp)
                    comp.signal.KILL.connect(lambda: selectables.remove(comp))
            def get_selected(selectables):
                for comp in selectables:
                    if comp.is_selected:
                        yield comp
            selected = property(get_selected)
        self.selectables = Selectables()

        self._can_select = False
        self._selection_rect_ref = lambda: None
        self._selection_rect_class = SelectionRectClass
        self._selectionrect_visibility = True
        self.selectionrect_layer = None

        self.connect("_interact_with_clipboard", self.signal.KEYDOWN)
        self.connect("close_selection", self.signal.DEFOCUS)
        self.connect("close_selection", self.signal.LINK)  # only usefull at link while focused

    is_selecting = property(lambda self: self._selection_rect_ref() is not None)
    selection_rect = property(lambda self: self._selection_rect_ref())

    def _interact_with_clipboard(self, key):

        if keyboard.mod.cmd:
            if key is pygame.K_a:
            # Cmd + a -> select all
                self.select_all()
            elif key is pygame.K_c:
            # Cmd + c -> copy selected data
                if self.is_selecting:
                    clipboard.put(self.get_selected_data())  # TODO : fix get_selected_data
            elif key is pygame.K_v:
            # Cmd + v -> paste clipboard data
                self.paste(clipboard.get(str) if clipboard.contains(str) else '')
            elif key is pygame.K_x:
            # Cmd + x -> copy and cut selected data
                if self.is_selecting:
                    clipboard.put(self.get_selected_data())
                    self.del_selected_data()

    def close_selection(self):

        if not self.is_selecting: return
        self.selection_rect.kill()
        for selectable in self.selectables.selected:
            if not selectable.is_selected: continue
            selectable._is_selected = False
            selectable.unselect()
            selectable.handle_unselect()

    def copy(self):
        """
        Copy the selected data in clipboard
        """
        data = self.get_selected_data()
        if data:
            clipboard.put(data)

    def cut(self):
        """
        To be overriden
        """

    def enable_selecting(self, can_select=True):
        """
        Completely delete the ability to make selections in a Selector
        """

        if bool(can_select) == self._can_select: return
        self._can_select = bool(can_select)
        if can_select:
            self.selectionrect_layer = Layer(self, self._selection_rect_class, name="selectionrect_layer",
                                             level=self.layers_manager.FOREGROUND, maxlen=1, touchable=False)
        else:
            self.close_selection()
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
        if visible is not None: self.selection_rect.set_visibility(visible)
        else:                   self.selection_rect.set_visibility(self._selectionrect_visibility)
        self.selection_rect.set_end((abs_pos[0], abs_pos[1]))
        for selectable in self.selectables:
            selectable.check_select(self.selection_rect)

    def get_selected_data(self):

        if not self.is_selecting: return None
        selected = tuple(s for s in self.selectables if s.is_selected)
        if not selected: return
        sorted_selected = sorted(selected, key=lambda o: (o.abs.top, o.abs.left))
        return '\n'.join(str(s.get_selected_data()) for s in sorted_selected)

    def handle_link_motion(self, link_motion_event):
        with paint_lock:
            if self.selection_rect is None:
                self.start_selection(link_motion_event.origin)
            self.end_selection(link_motion_event.pos)

    def paste(self, data):
        """
        This method is called when the user press Cmd + V
        data is the string content of the clipboard
        If the clipboard don't contains string data, then data is ''
        If you want to acces to other types of clipboard data, try :
        if clipboard.contains(type):
            data = clipboard.get(type)
        """

    def select_all(self):

        if self.selectables:
            if self.is_selecting:
                self.close_selection()
            self.start_selection(self.abs.topleft)
            self.end_selection(self.abs.bottomright, visible=False)

            # self.start_selection((
            #     min(s.abs.left for s in self.selectables),
            #     min(s.abs.top for s in self.selectables)
            # ))
            # self.end_selection((
            #     max(s.abs.right for s in self.selectables),
            #     max(s.abs.bottom for s in self.selectables)
            # ))

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
