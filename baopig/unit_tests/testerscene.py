

from baopig import *


class TesterScene(Scene):

    def __init__(self, app, ContentZoneClass):

        Scene.__init__(self, app, name=str(ContentZoneClass))
        self.sections = []

        # Menu
        self.menu_zone = Zone(self, size=(int(self.w / 2) - 15, 35), pos=(10, 10), name="menu")

        # Section
        self.sections_zone = Zone(self, size=(self.w/2-15, self.h-self.menu_zone.h-20), background_color="lightgray",
                                  pos=(10, self.menu_zone.bottom + 10), name="sections")
        GridLayer(self.sections_zone, name="sections_layer", col_width=self.sections_zone.w, nbcols=1)
        self.add_section(title="NO TEST SECTION YET", tests=[])

        # Run button
        def run():
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False) as script:
                script.write(self.try_it_yourself.code.text)
                script.seek(0)
                script.close()

                import subprocess
                with tempfile.TemporaryFile(mode="r") as output_file:
                    subprocess.call(f"python3 {script.name}", shell=True, stdout=output_file, stderr=output_file)
                    output_file.seek(0)
                    output = output_file.read()
                    self.try_it_yourself.console.set_text(str(output))
        self.run_tiy = Button(self, "RUN", command=run, sticky="topright", pos_ref=self.menu_zone, visible=False)

        # Back & Try_it_yourself buttons
        GridLayer(self.menu_zone, nbrows=1, children_margins=10)
        Button(self.menu_zone, "< BACK", col=0, command=PrefilledFunction(app.open, "UTMenu_Scene"))
        def try_it_yourself():
            if self.try_it_yourself.is_visible:
                self.try_it_yourself.hide()
                self.run_tiy.hide()
                self.sections_zone.show()
            else:
                self.try_it_yourself.show()
                self.run_tiy.show()
                self.sections_zone.hide()
        Button(self.menu_zone, "Try it yourself !", col=1, command=try_it_yourself)

        # Content
        self.content = ContentZoneClass(self, size=(self.w/2-15, self.h - 20), name="content",
                      pos=(-10, 10), sticky="topright")
        if hasattr(self.content, "load_sections"):
            self.content.load_sections()

        # Try it yourself
        self.try_it_yourself = None
        self._init_try_it_yourself()

    def _init_try_it_yourself(self):

        import inspect
        file = open(inspect.getfile(self.content.__class__), "r")
        content = file.read()
        file.close()

        content = content.split("\n\n# For the PresentationScene import")

        code = f"""# Default code for Try it yourself
{content[0]}

app = Application(size=(700, 700))
main_zone = {self.content.__class__.__name__}(Scene(app), size=("90%", "90%"), sticky="center")
app.launch()"""

        self.try_it_yourself = Zone(self, size=(self.w/2-15, self.h-20),
                                    pos=(10, self.menu_zone.bottom + 10), name="try_it_yourself")
        self.try_it_yourself.hide()
        self.try_it_yourself.code = TextEdit(self.try_it_yourself, text=code, width=self.try_it_yourself.w,
                                             font_file="monospace")
        window = pygame.Rect(self.try_it_yourself.code.rect)
        window.height = self.try_it_yourself.bottom - 400
        self.try_it_yourself.code.set_window(window)
        self.try_it_yourself.console = Text(self.try_it_yourself, max_width=self.try_it_yourself.w,
                                            font_file="monospace", pos=(0, window.bottom + 10),
                                            background_color=(211, 189, 189))

    def add_section(self, title, tests):

        if self.sections and self.sections[0] == ["NO TEST SECTION YET", []]:
            self.sections.pop(0)
            for temp in tuple(self.sections_zone.all_children):
                temp.kill()

        self.sections.append([title, tests])
        Text(self.sections_zone, "--- SECTION {} : {} ---".format(len(self.sections), title),
             font_height=self.theme.get_style_for(Text)["font_height"] + 2, font_bold=True,
             row=len(self.sections_zone.all_children), max_width=self.sections_zone.w)
        for i, text in enumerate(tests):
            CheckBox(self.sections_zone, text="TEST {} : ".format(i+1) + text,  # {:0>2} for 01, 02...
                     row=len(self.sections_zone.all_children), width=self.sections_zone.w)
        Text(self.sections_zone, "", row=len(self.sections_zone.all_children))

    def handle_scene_close(self):

        self.kill()

    def set_code(self, code):
        self.try_it_yourself.code.set_text(code)

