

from baopig import *


# --- DEBUG ---
class DebugZone(Zone, Closable):

    def __init__(self, scene):

        Zone.__init__(
            self,
            parent=scene,
            size=scene.size,
            background_color=(0, 0, 0, 0),
            layer=scene.debug_layer
        )

        self.set_style_for(Text, color="black")

        self._pointed = None
        self.highlighter = None

        h = 200
        self.debug_zone = Zone(
            parent=self,
            size=(self.w - 10, h),
            background_color=(255, 255, 255, 145),
            name=self.name + " -> debug_zone",
            pos=(5, -5), pos_location="bottomleft", pos_ref_location="bottomleft"
        )
        # TODO : self.debug_zone.style.font.file = None

        presentators_zone = Zone(
            parent=self.debug_zone,
            pos=(5, 5),
            size=(80, self.debug_zone.h),
            name=self.debug_zone.name + " -> presentators_zone"
        )
        trackers_zone = Zone(
            parent=self.debug_zone,
            pos=(presentators_zone.right, 5),
            size=(4000, self.debug_zone.h),  # TODO : how to say 'I define the height but not the width ?' or 'width adapts to the cell'
            name=self.debug_zone.name + " -> trackers_zone"
        )

        if True:
            # FPS TRACKER
            fps_presentator = Text(
                parent=presentators_zone,
                text="FPS : ",
                pos=(0, 5),
                name="FPS_presentator")
            DynamicText(
                parent=trackers_zone,
                get_text=lambda: self.parent.painter.get_current_fps(),
                pos=(0, fps_presentator.top),
                name="FPS_tracker")

            # MOUSE TRACKER
            mouse_pos_presentator = Text(
                parent=presentators_zone,
                text="Mouse : ",
                pos=(0, fps_presentator.bottom),
                name="mouse_pos_presentator")
            DynamicText(
                parent=trackers_zone,
                get_text=PrefilledFunction(lambda: mouse.pos),
                pos=(0, mouse_pos_presentator.top),
                name="mouse_pos_tracker")

            pointed_comp_presentator = Text(
                parent=presentators_zone,
                text="Hovered : ",
                pos=(0, mouse_pos_presentator.bottom),
                name="pointed_comp_presentator")

            # NAME TRACKER
            name_presentator = Text(
                parent=presentators_zone,
                text="- name : ",
                pos=(0, pointed_comp_presentator.bottom),
                name="name_presentator")
            DynamicText(
                parent=trackers_zone,
                get_text=lambda: mouse.pointed_comp.name if mouse.pointed_comp else None,
                pos=(0, name_presentator.top),
                name="name_tracker")

            # HITBOX TRACKER
            hitbox_presentator = Text(
                parent=presentators_zone,
                text="- hitbox : ",
                pos=(0, name_presentator.bottom),
                name="hitbox_presentator")
            DynamicText(
                parent=trackers_zone,
                get_text=lambda: mouse.pointed_comp.hitbox if mouse.pointed_comp else None,
                pos=(0, hitbox_presentator.top),
                name="hitbox_tracker")

            # PARENT TRACKER
            parent_presentator = Text(
                parent=presentators_zone,
                text="- parent : ",
                pos=(0, hitbox_presentator.bottom),
                name="parent_presentator")
            DynamicText(
                parent=trackers_zone,
                get_text=lambda: mouse.pointed_comp.parent if mouse.pointed_comp else None,
                pos=(0, parent_presentator.top),
                name="parent_tracker")

            # POINTED TRACKER
            # pointed_presentator = Text(
            #     parent=presentators_zone,
            #     text="Pointed : ",
            #     pos=(0, parent_presentator.bottom),
            #     name="pointed_presentator")
            # DynamicText(
            #     parent=trackers_zone,
            #     get_text=lambda: repr(mouse._get_pointed_comp()),
            #     pos=(0, pointed_presentator.top),
            #     name="pointed_tracker")

            # TODO : mouse.pointed_comp tracker

        self.print_text = Text(
            parent=self.debug_zone,
            text="This text is aimed to debug",
            pos=(5, self.debug_zone.h - 5 - 15),
            name=self.debug_zone.name + " -> print_text"
        )

        # TODO : grid pack with margin

        def print_pointed_comp(*args):
            if hasattr(mouse.pointed_comp.parent, "text"):
                self.print(mouse.pointed_comp.parent.text)
            # self.print(repr(mouse.pointed_comp))
        # self.handle_keydown[keyboard.SPACE].add(print_pointed_comp)

        self.connect("update", self.parent.signal.RESIZE)
        self.connect("update_pointed_outline", mouse.signal.MOTION)
        self.connect("update_pointed_outline", mouse.signal.DRAG)

        self.update_pointed_outline()
        self.debug_zone.adapt(self.debug_zone.default_layer, horizontally=False)
        self.set_nontouchable()
        self.set_always_dirty()

    is_debugging = property(lambda self: not self.is_sleeping)

    def asleep(self):

        self.highlighter.hide()
        super().asleep()

    def close(self):

        self.kill()

    def print(self, obj):

        self.print_text.set_text(str(obj))
        self.debug_zone.adapt(self.debug_zone.default_layer, horizontally=False)

    def start_debugging(self):

        if self.is_debugging:
            return

        self.wake()

    def stop_debugging(self):

        if not self.is_debugging:
            return

        self.asleep()

    def toggle_debugging(self):

        if self.is_debugging:
            self.stop_debugging()
        else:
            self.start_debugging()

    def update(self, old_size):

        self.resize(*self.parent.size)
        self.debug_zone.resize_width(self.size[0] - 10)
        self.update_pointed_outline()

    def update_pointed_outline(self, *args):

        pointed = mouse.pointed_comp
        if pointed and self.is_awake:
            if self._pointed == pointed: return
            self._pointed = pointed
            if self.highlighter is None:
                self.highlighter = Highlighter(
                    parent=self,
                    target=self._pointed,
                    color=(0, 255, 0),
                    width=1,
                    name=self.name + ".highlighter"
                )
                self.highlighter.move_behind(self.debug_zone)
            else:
                self.highlighter.config(target=self._pointed)
        else:
            self._pointed = None
            if self.highlighter is not None:
                self.highlighter.hide()

    def wake(self):

        self.highlighter.show()
        super().wake()
        self.update_pointed_outline()

