

from baopig._lib import Zone, Application
from baopig.widgets.textedit import TextEdit


class UT_InputText_Zone(Zone):

    def __init__(self):

        Zone.__init__(self)

        TextEdit(self, pos=(10, 10))


ut_zones = [
    UT_InputText_Zone,
]

if __name__ == "__main__":
    from baopig.unit_tests.testerscene import TesterScene
    app = Application()
    for scene in ut_zones:
        TesterScene(app, scene)
    app.launch()
