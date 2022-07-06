from typing import Iterable


class Communicative:
    """
    Class for objects who need to emit signals

    :Example:
    ---------
        class Transmitter(bp.Communicative):
            def __init__(self, message):
                bp.Communicative.__init__(self)
                self.message = message
                self.create_signal("EMISSION")
            def transmit(self):
                self.signal.EMISSION.emit(self.message)

        class Listener(bp.Communicative):
            def receive(self, message):
                print(f"Message received: {message}")

        my_transmitter = Transmitter("Hello world !")
        my_listener = Listener()
        my_transmitter.signal.EMISSION.connect(my_listener.receive, owner=my_listener)
        my_transmitter.transmit()  # prints : 'Message received: Hello world !'
        my_listener.disconnect()
        my_transmitter.transmit()  # prints nothing

    :Attributes:
    ------------
        signal: object -> an object containing all the signals

    :Methods:
    ---------
        create_signal(signal_id) -> creates a signal accessible via 'signal_id'
        disconnect()             -> kills all the connections owned by this object
    """

    def create_signal(self, signal_id: str):
        """
        Creates a signal accessible via 'signal_id'
        'signal_id' must be an uppercase string

        After obj.create_signal("EMISSION"), the created signal is accessed this way:
            obj.signal.EMISSION
        """

    def disconnect(self):
        """ Kills all the connections owned by this object """


class Widget(Communicative):
    """
    Abstract class for the graphical elements of the screen
    A widget can be visible, hidden, awake, sleeping, alive, or dead
    A widget has only one parent (baopig bio-logic, hmmm...)
    A widget has to initialize its surface at its creation

    :Signals:
    ---------
        HIDE: emitted when the widget's visibility state goes from visible to hidden
        KILL: emitted when the widget gets killed
        SHOW: emitted when the widget's visibility state goes from hidden to visible
        SLEEP: emitted when the widget's sleeping state goes from awake to asleep
        WAKE: emitted when the widget's sleeping state goes from asleep to awake

    :Attributes:
    ------------
        parent: Container -> the manager

        surface: pygame.Surface -> the widget's appearance
        rect: pygame.Rect:      -> the widget's size
        hitbox: pygame.Rect:    -> the widget's size on the screen

        pos: tuple  # TODO
        pos_loc: WidgetLocation
        pos_ref: Widget
        pos_ref_loc: WidgetLocation

        is_alive: bool   -> True if the widget has not been killed
        is_asleep: bool  -> True if the widget is asleep
        is_awake: bool   -> True if the widget is not asleep
        is_dead: bool    -> True if the widget has been killed
        is_hidden: bool  -> True if the widget is not visible
        is_visible: bool -> True if the widget is visible

    :Methods:
    ---------
        set_pos(pos=None, pos_loc=None, pos_ref_loc=None) -> moves the widget  # TODO
            # pos = pos + pos_ref.abs.pos_ref_loc - parent.abs.topleft
            # rect.pos_loc = pos
            # signal.MOTION.emit()

        set_size(width, height) -> resizes the widget  # TODO
            # rect.size = width, height
            # signal.RESIZE.emit()

        hide()  -> the widget is no longer visible
        kill()  -> the widget is permanently deleted
        show()  -> the widget is visible again
        sleep() -> the widget is detached from its parent
        wake()  -> the widget is reattached to its parent

        send_display_request(rect=None) -> sends a request who will update the display
    """

    def hide(self):
        """
        Stops displaying the widget

        Behaviour:
        ----------
            Sets visibility to False
            Sends a display request
            Emits the HIDE signal
        """

    def kill(self):
        """
        Kills the widget
        A killed widget should not be used ever again

        Behaviour:
        ----------
            Emits the KILL signal
            Detaches the widget from its parent
            Kills all the connections owned by the widget
            Kills the widget's weakref
        """

    def send_display_request(self, rect: Iterable[int] | None):
        """
        Sends a request who will update the display
        rect represents a pygame.Rect object
        rect must be referenced by the widget's parent
        If rect is not set, the widget's hitbox will be used
        Only the screen's portion corresponding to rect will be updated
        """

    def show(self):
        """
        Starts to display the widget again

        Behaviour:
        ----------
            Sets visibility to True
            Sends a display request
            Emits the SHOW signal
        """

    def sleep(self):
        """
        Detaches the widget from its parent
        A sleeping widget cannot move

        Behaviour:
        ----------
            Detaches the widget from its parent
            Emits the SLEEP signal
        """

    def wake(self):
        """
        Reattaches the widget to its parent

        Behaviour:
        ----------
            If the parent got killed:
                Kills the widget
            Attaches the widget to its parent
            Updates the widget's size & position
            Emits the WAKE signal
        """


class Hoverable(Widget):
    """
    Class for widgets who need to handle when they are hovered or unhovered by the mouse.

    A Hoverable can have an Indicator, i.e. a Text that appears when the Hoverable is hovered.
    For more details, see TODO : link to Indicator documentation

    :Signals:
    ---------
        HOVER: emitted when the widget gets hovered by the mouse
        UNHOVER: emitted when the widget gets unhovered from the mouse

    :Attributes:
    ------------
        is_hovered: bool     -> True if the mouse is hovering the widget
        indicator: Indicator -> the widget's indicator, not always set

    :Methods:
    ---------
        handle_hover()   -> abstract - called when the widget gets hovered by the mouse
        handle_unhover() -> abstract - called when the widget gets unhovered from the mouse
    """

    def handle_hover(self):
        """ Abstract - called when the widget gets hovered by the mouse """

    def handle_unhover(self):
        """ Abstract - called when the widget gets unhovered from the mouse """


# ...


class Container(Widget):
    """
    Widgets parent

    Attributes:
    -----------
        children: list -> the list of all the children
    """


class Layout(Container):
    """
    Widgets's size and position manager

    Attributes:
    -----------
        padding: Margin
        spacing: Margin

        content_rect: pygame.Rect -> the space for children

    """


class Zone(Container):
    """
    Convenient Widgets manager

    Attributes:
    -----------
        background: Layer
        content: Layer
        foreground: Layer
    """


class Scene(Zone):
    """
    An application frame

    Methods:
        open
    """
