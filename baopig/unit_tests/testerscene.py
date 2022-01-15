

from baopig import *


class TesterScene(Scene):

    def __init__(self, app, ContentZoneClass):

        # TODO : finish to automatically collect every UT_Scene
        # TODO : button Home

        Scene.__init__(self, app, size=(900, 600), name=str(ContentZoneClass))
        self.sections = []
        # TODO : automatically pack zones with margin

        # Menu
        self.menu_zone = Zone(self, size=(self.w-20, 25), pos=(10, 10), name="menu")
        GridLayer(self.menu_zone, nbrows=1)  # TODO : margin
        Button(self.menu_zone, "< BACK", col=0, command=PrefilledFunction(app.open, "UTMenu_Scene"))
        def try_it_yourself():
            if self.try_it_yourself.is_visible:
                self.try_it_yourself.hide()
            else:
                self.try_it_yourself.show()
        Button(self.menu_zone, "Try it yourself !", col=1,
               command=try_it_yourself)

        # Section
        self.sections_zone = Zone(self, size=(self.w/2-15, self.h-self.menu_zone.h-20), background_color="lightgray",
                                  pos=(10, self.menu_zone.bottom + 10), name="sections")
        # TODO : MenuLayer or ColumnLayer, just a Grid with one column
        GridLayer(self.sections_zone, name="sections_layer", col_width=self.sections_zone.w, nbcols=1)
        self.add_section(title="NO TEST SECTION YET", tests=[])

        # Try it yourself
        self.try_it_yourself = None
        self._init_try_it_yourself()

        # Content
        self.content = ContentZoneClass(self, size=(self.w/2-15, self.h-self.menu_zone.h-20), name="content",
                      pos=(-10, self.menu_zone.bottom + 10), sticky="right")

    def _init_try_it_yourself(self):

        code = """# Default code for Try it yourself

from baopig import *

app = Application()
scene = Scene(app)

def click():
    print("Hello world")
b = Button(scene, "Hello world", command=click)

app.launch()"""

        self.try_it_yourself = Zone(self, size=(self.w/2-15, self.h-20), background_color="lightgray",
                                    pos=(10, self.menu_zone.bottom + 10), name="try_it_yourself")
        self.try_it_yourself.hide()
        self.try_it_yourself.code = TextEdit(self.try_it_yourself, width=self.try_it_yourself.w,
                                                 text=code, font=Font(file="monospace"))  # TODO : font_file

        self.try_it_yourself.console = Text(self.try_it_yourself, pos=(0, "50%"))

        # TODO : TextEdit and LineEdit
        # TODO : CodeEdit
        def run():
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".py", mode="w") as script:
                script.write(self.try_it_yourself.code.text)
                script.seek(0)

                import subprocess
                with tempfile.TemporaryFile(mode="r") as output_file:
                    subprocess.call("python3 {}".format(script.name), shell=True, stdout=output_file, stderr=output_file)
                    output_file.seek(0)
                    output = output_file.read()

                    # proc = subprocess.Popen(['python3', script.name], stdout=output_file, shell=True)
                    # data = proc.communicate()
                    # # proc.run()
                    # output_file.seek(0)
                    # output = output_file.read()
                    self.try_it_yourself.console.set_text(str(output))

        self.try_it_yourself.run = Button(self.try_it_yourself, "RUN",
                                          sticky="right", command=run, catching_errors=False)

    def add_section(self, title, tests):

        if self.sections and self.sections[0] == ["NO TEST SECTION YET", []]:
            self.sections.pop(0)
            for temp in tuple(self.sections_zone.children):
                temp.kill()

        self.sections.append([title, tests])
        ressources.font.config(file="Gill Sans MT")
        Text(self.sections_zone, "--- SECTION {} : {} ---".format(len(self.sections), title),
             font_height=ressources.font.height+2, bold=True,
             row=len(self.sections_zone.children), max_width=self.sections_zone.w)
        for i, text in enumerate(tests):
            # TODO : CheckBoxes
            Text(self.sections_zone, text="TEST {} : ".format(i+1) + text,  # {:0>2} for 01, 02...
                 row=len(self.sections_zone.children), max_width=self.sections_zone.w)
        Text(self.sections_zone, "", row=len(self.sections_zone.children))

    def set_code(self, code):
        self.try_it_yourself.code.set_text(code)

