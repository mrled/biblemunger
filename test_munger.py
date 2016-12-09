import json
import unittest

import munger


class MungerTestCase(unittest.TestCase):

    # def test_MakoHandler(self):
    #     raise Exception("TODO: implement test_MakoHandler()")

    # def test_MakoLoader(self):
    #     raise Exception("TODO: implement test_MakoLoader()")

    def test_DictEncoder(self):
        class TestClass(object):
            def __init__(self):
                self.a = 1
                self.b = 2
                self.c = [3, 33, 333]
                self.d = {'f': 4, 'fo': 44, 'fou': 444, 'four': 4444}
                self.e = 'F I V E'
        testobj = TestClass()
        # Be careful that your keys are sorted
        testjson = '''{"a": 1, "b": 2, "c": [3, 33, 333], "d": {"f": 4, "fo": 44, "fou": 444, "four": 4444}, "e": "F I V E"}'''
        parsedjson = json.dumps(testobj, cls=munger.DictEncoder, sort_keys=True)
        if testjson != parsedjson:
            raise Exception("\n".join((
                "Loaded JSON object did not match test object:",
                "    Loaded:    " + parsedjson,
                "    Expected:  " + testjson)))

    # def test_BibleMungingServer(self):
    #     raise Exception("implement test_BibleMungingServer()")
