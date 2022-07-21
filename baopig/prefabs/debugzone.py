from baopig import mouse
from baopig import Zone, Handler_SceneClose, Text, DynamicText, Highlighter


# --- DEBUG ---
class DebugZone(Zone, Handler_SceneClose):

    def __init__(self, scene):

        Zone.__init__(self, scene, size=scene.size, background_color=(0, 0, 0, 0), layer=scene.debug_layer,
                      touchable=False)

        self.set_style_for(Text, font_color="black", font_file=None)

        self._pointed = None
        self.highlighter = None

        h = 200
        self.debug_zone = Zone(
            parent=self,
            size=(self.rect.w - 10, h),
            background_color=(255, 255, 255, 145),
            name=self.name + " -> debug_zone",
            bottomleft=(5, -5), refloc="bottomleft"
        )

        presentators_zone = Zone(
            parent=self.debug_zone,
            pos=(5, 5),
            size=(120, self.debug_zone.rect.h),
            name=self.debug_zone.name + " -> presentators_zone"
        )
        trackers_zone = Zone(
            parent=self.debug_zone,
            pos=(presentators_zone.rect.right, 5),
            size=(4000, self.debug_zone.rect.h),
            name=self.debug_zone.name + " -> trackers_zone"
        )

        if True:
            # FPS TRACKER
            Text(presentators_zone, text="FPS : ")
            DynamicText(trackers_zone, get_text=lambda: self.parent.painter.get_current_fps())

            # MOUSE TRACKER
            Text(presentators_zone, text="Mouse pos : ")
            DynamicText(trackers_zone, get_text=lambda: mouse.pos)

            Text(presentators_zone, text="Pointed widget : ")
            Text(trackers_zone)

            # CLASS TRACKER
            Text(presentators_zone, text="- class : ")
            DynamicText(trackers_zone, get_text=lambda: self._pointed.__class__.__name__ if self._pointed else None)

            # NAME TRACKER
            Text(presentators_zone, text="- name : ")
            DynamicText(trackers_zone, get_text=lambda: self._pointed.name if self._pointed else None)

            # HITBOX TRACKER
            Text(presentators_zone, text="- hitbox : ")
            DynamicText(trackers_zone, get_text=lambda: self._pointed.hitbox if self._pointed else None)

            # HITBOX TRACKER
            Text(presentators_zone, text="- abs_hitbox : ")
            DynamicText(trackers_zone, get_text=lambda: self._pointed.abs_hitbox if self._pointed else None)

            # PARENT TRACKER
            Text(presentators_zone, text="- parent : ")
            DynamicText(trackers_zone, get_text=lambda: self._pointed.parent if self._pointed else None)

        presentators_zone.pack()
        trackers_zone.pack()

        self.print_text = Text(
            parent=self.debug_zone,
            text="This text is aimed to debug",
            pos=(5, self.debug_zone.rect.h - 5 - 15),
            name=self.debug_zone.name + " -> print_text"
        )

        self.parent.signal.RESIZE.connect(self.handle_scene_resize, owner=self)
        mouse.signal.MOUSEMOTION.connect(self.update_pointed_outline, owner=self)

        self.update_pointed_outline()
        self.debug_zone.adapt(self.debug_zone.default_layer, horizontally=False)

    is_debugging = property(lambda self: self.is_awake)

    def handle_scene_close(self):

        self.kill()  # TODO : not kill

    def handle_scene_resize(self):

        self.resize(*self.scene.size)
        self.debug_zone.resize_width(self.rect.w - 10)
        self.update_pointed_outline()

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

        self.sleep()

    def toggle_debugging(self):

        if self.is_debugging:
            self.stop_debugging()
        else:
            self.start_debugging()

    def update_pointed_outline(self):

        def collidemouse(widget):
            return widget.is_visible and widget.abs_hitbox.collidepoint(mouse.pos)

        def get_pointed_widget(cont):

            for layer in reversed(tuple(cont.layers_manager.touchable_layers)):
                assert layer.touchable
                for child in reversed(layer):
                    if child is self:
                        continue
                    if collidemouse(child):
                        if hasattr(child, "children"):
                            return get_pointed_widget(child)
                        return child
            return cont

        if self.is_asleep:
            return

        pointed = get_pointed_widget(self.scene)
        if pointed:
            if self._pointed == pointed:
                return
            self._pointed = pointed
            if self.highlighter is not None:
                self.highlighter.kill()
            self.highlighter = Highlighter(parent=self, target=pointed, name=self.name + ".highlighter")
            self.highlighter.move_behind(self.debug_zone)
        else:
            self._pointed = None

    def wake(self):

        super().wake()
        self.update_pointed_outline()
