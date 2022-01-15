import unittest
import docs as bp


class ApplicationClassTest(unittest.TestCase):
    def setUp(self):
        self.app = bp.Application()

    def test_set_fps(self):
        self.app.set_fps(30)
        self.assertEqual(self.app.fps, 30)

        self.app.set_fps(60)
        self.assertEqual(self.app.fps, 60)


if __name__ == '__main__':
    unittest.main()
