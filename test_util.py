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

    def setUp(self):
        self.dburi = "file:TESTING_MEMORY_DB?mode=memory&cache=shared"
        self.lockableconn = util.LockableSqliteConnection(self.dburi)

    def tearDown(self):
        self.lockableconn.close()

    def test_lsc(self):
        with self.lockableconn.ro as dbconn:
            dbconn.cursor.execute("SELECT 1")
            result = dbconn.cursor.fetchone()[0]
        self.assertEqual(result, 1)

    # def test_locking(self):
    #     raise Exception("TODO: test the locking behavior somehow")


class MiscFunctionsTestCase(unittest.TestCase):

    def test_normalizewhitespace(self):
        self.assertEqual(util.normalizewhitespace("q w e r"), "q w e r")
        self.assertEqual(util.normalizewhitespace("q  w e r"), "q w e r")
        self.assertEqual(util.normalizewhitespace("""
            q  w
            e r"""), "q w e r")
        self.assertEqual(util.normalizewhitespace("q {} w e r", 1), "q 1 w e r")
        self.assertEqual(util.normalizewhitespace("q {} w {} e r", (1, 2)), "q 1 w 2 e r")
        self.assertEqual(util.normalizewhitespace("q {} w e r", "one"), "q one w e r")
