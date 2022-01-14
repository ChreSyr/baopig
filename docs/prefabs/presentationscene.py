
from baopig.pybao.objectutilities import PrefilledFunction
from baopig import *
from baopig.unit_tests.testerscene import TesterScene



class PresentationScene(Scene):

    def __init__(self, app):

        Scene.__init__(self, app)

        GridLayer(self)

        Text(self, text="", row=len(self.default_layer))
        Text(self, text="Welcome to baopig version {}".format(version), row=len(self.default_layer))
        Text(self, text="You can look for the tutorial or experiment unit tests", row=len(self.default_layer))
        Text(self, text="", row=len(self.default_layer))

        Button(self, text="Unit Tests", command=PrefilledFunction(app.open, "UTMenu_Scene"),
               row=len(self.default_layer))
        Button(self, text="Tutorial", row=len(self.default_layer))

        UTMenu_Scene(app)


class UTMenu_Scene(Scene):

    def __init__(self, app):

        Scene.__init__(self, app)

        # l = MenuLayer(self)  # TODO
        GridLayer(self)

        Text(self, text="", row=0)
        Text(self, text="Which class do you want to test ?", row=1)
        Text(self, text="", row=2)

        back = Button(self, "Menu", command=PrefilledFunction(app.open, "PresentationScene"), col=1)
        back.bottomright = self.bottomright

        def get_ut_filenames():
            import os
            dir = os.path.dirname(os.path.realpath(__file__))[:-7] + "unit_tests"
            for root, dirs, files in os.walk(dir):
                for filename in files:
                    if filename.endswith(".py") and filename.startswith("ut_"):
                        yield filename[:-3]  # discard '.py'

        import importlib
        for filename in get_ut_filenames():
            print(filename)
            if filename in ("testerscene", "ut_baopig"):
                continue
            ut_file = importlib.import_module("baopig.unit_tests." + filename)
            # exec("from {} import get_ut_scenes".format(path))
            # from path import get_ut_scenes
            for zone in ut_file.ut_scenes:  # TODO : replace ut_scenes by ut_zones
                scene = TesterScene(app, zone)
                Button(self, row=len(self.default_layer), text=filename[3:],  # discard 'ut_'
                       command=PrefilledFunction(app.open, scene.name))
