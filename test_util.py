import json
import unittest

import util


# TODO: like, write the Mako tests okay
# class MakoBullshitTestCase(unittest.TestCase):

#     def test_MakoHandler(self):
#         raise Exception("TODO: implement test_MakoHandler()")

#     def test_MakoLoader(self):
#         raise Exception("TODO: implement test_MakoLoader()")


class DictEncoderTestCase(unittest.TestCase):

    class TestClass(object):

        def __init__(self):
            self.a = 1
            self.b = 2
            self.c = [3, 33, 333]
            self.d = {'f': 4, 'fo': 44, 'fou': 444, 'four': 4444}
            self.e = 'F I V E'

    def test_encoder(self):

        testobj = self.TestClass()
        # Be careful that your keys are sorted
        testjson = '''{"a": 1, "b": 2, "c": [3, 33, 333], "d": {"f": 4, "fo": 44, "fou": 444, "four": 4444}, "e": "F I V E"}'''
        parsedjson = json.dumps(testobj, cls=util.DictEncoder, sort_keys=True)
        self.assertEqual(testjson, parsedjson)


class LockableSqliteConnectionTestCase(unittest.TestCase):

    def test_lsc(self):
        dburi = "file:TESTING_MEMORY_DB?mode=memory&cache=shared"
        lockableconn = util.LockableSqliteConnection(dburi)
        with lockableconn as dbconn:
            dbconn.cursor.execute("SELECT 1")
            result = dbconn.cursor.fetchone()[0]
        self.assertEqual(result, 1)
