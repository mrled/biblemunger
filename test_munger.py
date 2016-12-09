import json
import unittest

import bible
import munger


# TODO: like, write the Mako tests okay
# class MakoBullshitTestCase(unittest.TestCase):

#     def test_MakoHandler(self):
#         raise Exception("TODO: implement test_MakoHandler()")

#     def test_MakoLoader(self):
#         raise Exception("TODO: implement test_MakoLoader()")


class DictEncoderTestCase(unittest.TestCase):

    def test_encoder(self):
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


class LockableSqliteConnectionTestCase(unittest.TestCase):

    def test_lsc(self):
        dburi = "file:TESTING_MEMORY_DB?mode=memory&cache=shared"
        lockableconn = munger.LockableSqliteConnection(dburi)
        with lockableconn as dbconn:
            dbconn.cursor.execute("SELECT 1")
            result = dbconn.cursor.fetchone()[0]
        if result != 1:
            raise Exception("Expected result to be '1' but was '{}'".format(result))


class BibleMungingServerTestCase(unittest.TestCase):

    dburi = "file:TESTING_MEMORY_DB?mode=memory&cache=shared"
    lockableconn = munger.LockableSqliteConnection(dburi)
    create_table_stmt = "CREATE TABLE recent_searches (search, replace)"

    def test_initialize_database(self):
        bib = bible.Bible(self.lockableconn.connection)
        faves = [
            {'search': 'search one', 'replace': 'replace one'},
            {'search': 'search two', 'replace': 'replace two'},
            {'search': 'search tre', 'replace': 'replace tre'}]
        bms = munger.BibleMungingServer(self.lockableconn, bib, faves, "app title", "app subtitle", wordfilter=False)
        bms.initialize_database()
        recents_tablename = bms.tablenames['recents']
        with self.lockableconn as dbconn:
            dbconn.cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='{}'".format(recents_tablename))
            result = dbconn.cursor.fetchone()
        if result[0] != self.create_table_stmt:
            raise Exception("Database initialization failed; expected '{}' but found '{}'".format(self.create_table_stmt, result))
