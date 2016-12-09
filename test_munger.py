import json
import unittest

import munger


class MungerTestCase(unittest.TestCase):

    # def test_MakoHandler(self):
    #     raise Exception("TODO: implement test_MakoHandler()")

    # def test_MakoLoader(self):
    #     raise Exception("TODO: implement test_MakoLoader()")

    def test_DictEncoder(self):
        testobj = {
            '1one': 1,
            '2two': 2,
            '3threes': [3, 33, 333],
            '4fours': {'f': 4, 'fo': 44, 'fou': 444, 'four': 4444, 'fours': 44444},
            '5five': 'F I V E'
        }
        # Be careful that your keys are sortable
        testjson = """{"1one": 1, "2two": 2, "3threes": [3, 33, 333], "4fours": {"f": 4, "fo": 44, "fou": 444, "four": 4444, "fours": 44444}, "5five": "F I V E"}"""
        parsedjson = json.dumps(testobj, cls=munger.DictEncoder, sort_keys=True)
        if testjson != parsedjson:
            raise Exception("\n".join((
                "Loaded JSON object did not match test object:",
                "    Loaded:    " + parsedjson,
                "    Expected:  " + testjson)))

    # def test_BibleMungingServer(self):
    #     raise Exception("implement test_BibleMungingServer()")
