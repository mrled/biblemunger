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
        self.assertEqual(result, 1)


class BibleMungingServerTestCase(unittest.TestCase):

    def setUp(self):
        self.dburi = "file:TESTING_MEMORY_DB?mode=memory&cache=shared"
        self.dbconn = munger.LockableSqliteConnection(self.dburi)

    def tearDown(self):
        self.dbconn.connection.close()

    def test_object_init_nofilter(self):
        apptitle = "test app title"
        appsubtitle = "test app subtitle"
        faves = [
            {'search': 'search one', 'replace': 'replace one'},
            {'search': 'search two', 'replace': 'replace two'},
            {'search': 'search tre', 'replace': 'replace tre'}]
        bib = bible.Bible(self.dbconn.connection)
        bms = munger.BibleMungingServer(self.dbconn, bib, faves, apptitle, appsubtitle, wordfilter=False)
        self.assertEqual(faves, bms.favorite_searches)
        self.assertEqual(apptitle, bms.apptitle)
        self.assertEqual(appsubtitle, bms.appsubtitle)
        self.assertNotIn('add_words', dir(bms.wordfilter))

    def test_object_init_filter(self):
        testword = 'QwertyStringUsedForTestingZxcvb'
        bib = bible.Bible(self.dbconn.connection)
        bms = munger.BibleMungingServer(self.dbconn, bib, [], "apptitle", "appsubtitle", wordfilter=True)
        self.assertIn('add_words', dir(bms.wordfilter))
        self.assertFalse(bms.wordfilter.blacklisted(testword))
        bms.wordfilter.add_words([testword])
        self.assertTrue(bms.wordfilter.blacklisted(testword))

    def test_initialize_database(self):
        create_table_stmt = "CREATE TABLE recent_searches (search, replace)"
        bib = bible.Bible(self.dbconn.connection)
        bms = munger.BibleMungingServer(self.dbconn, bib, [], "app title", "app subtitle", wordfilter=False)
        bms.initialize_database()
        recents_tablename = bms.tablenames['recents']
        with self.dbconn as dbconn:
            dbconn.cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='{}'".format(recents_tablename))
            result = dbconn.cursor.fetchone()
        self.assertEqual(result[0], create_table_stmt)

    def test_recent_searches(self):
        bib = bible.Bible(self.dbconn.connection)
        bms = munger.BibleMungingServer(self.dbconn, bib, [], "app title", "app subtitle", wordfilter=False)
        bms.initialize_database()
        recents = [
            ('search one', 'replace one'),
            ('search two', 'replace two'),
            ('search tre', 'replace tre')]
        with self.dbconn as dbconn:
            for recent in recents:
                dbconn.cursor.execute("INSERT INTO {} VALUES (?, ?)".format(bms.tablenames['recents']), (recent[0], recent[1]))
        with self.dbconn as dbconn:
            dbconn.cursor.execute("SELECT * FROM {}".format(bms.tablenames['recents']))
            results = dbconn.cursor.fetchall()
        self.assertEqual(recents, results)
