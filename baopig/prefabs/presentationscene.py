
from baopig import *
from baopig.version.version import version
from baopig.prefabs.testerscene import TesterScene


class PresentationScene(Scene):

    def __init__(self, app):

        Scene.__init__(self, app)

        app.set_debug(averagefps=True, launchtime=True)

        Text(self, text="")
        Text(self, text=f"Welcome to baopig version {version}")
        Text(self, text="You can look for the tutorial or experiment unit tests")
        Button(self, text="Unit Tests", command=PrefilledFunction(app.open, "UTMenu_Scene"),
               row=len(self.default_layer))
        Button(self, text="Tutorial")
        self.pack()
        UTMenu_Scene(app)
        self.open()  # without this line, UTMenu_Scene is the first scene, since this one has not been added yet


class UTMenu_Scene(Scene):

    def __init__(self, app):

        Scene.__init__(self, app)

        GridLayer(self)

        Text(self, text="", row=0)
        Text(self, text="Which class do you want to test ?", row=1)
        Text(self, text="", row=2)

        Button(self, "Menu", command=PrefilledFunction(app.open, "PresentationScene"), col=1)

        def get_ut_filenames():
            import os
            directory = os.path.dirname(os.path.realpath(__file__))[:-7] + "unit_tests"
            for root, dirs, files in os.walk(directory):
                for file_name in files:
                    if file_name.endswith(".py") and file_name.startswith("ut_"):
                        yield file_name[:-3]  # discard '.py'

        import importlib
        for filename in get_ut_filenames():
            ut_file = importlib.import_module("baopig.unit_tests." + filename)
            try:
                zone_class = ut_file.ut_zone_class

                def open_testerscene(zc):
                    TesterScene(app, zc).open()

                Button(self, row=len(self.default_layer), text=zone_class.__name__[3:-5],  # discards 'UT_' and '_Zone'
                       command=PrefilledFunction(open_testerscene, zone_class), catching_errors=False)  # TODO : True
            except AttributeError:
                pass


if __name__ == "__main__":
    Application().launch()
