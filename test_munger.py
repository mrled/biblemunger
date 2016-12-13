import json
import unittest

import cherrypy
from wordfilter import Wordfilter

import bible
import munger
import util


# class FrontEndServerTestCase(unittest.TestCase):

#     def test_munge_page(self):
#         raise Exception("TODO: implement test_munge_page")


class ApiServerTestCase(unittest.TestCase):

    def setUp(self):
        self.dburi = "file:TESTING_MEMORY_DB?mode=memory&cache=shared"
        self.dbconn = util.LockableSqliteConnection(self.dburi)
        self.bible = bible.Bible(self.dbconn)
        self.censor = munger.ImpotentCensor()
        self.apiserver = munger.ApiServer(self.dbconn, self.bible, self.censor)

    def tearDown(self):
        self.dbconn.close()

    def test_object_init(self):
        self.assertIsInstance(self.apiserver.recents, munger.SavedSearches)
        self.assertIsInstance(self.apiserver.favorites, munger.SavedSearches)
        self.assertIsInstance(self.apiserver.version, munger.VersionApi)
        self.assertIsInstance(self.apiserver.search, munger.BibleSearchApi)

    # def test_GET(self):
    #     raise Exception("TODO: Test the GET method")

    def test_initialize_database(self):
        recents_stmt = "CREATE TABLE recent_searches (search, replace)"
        favorites_stmt = "CREATE TABLE favorite_searches (search, replace)"
        self.apiserver.initialize_database()
        with self.dbconn as dbconn:
            dbconn.cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='{}'".format(self.apiserver.tablenames['recents']))
            recents_result = dbconn.cursor.fetchone()[0]
            dbconn.cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='{}'".format(self.apiserver.tablenames['favorites']))
            favorites_result = dbconn.cursor.fetchone()[0]
        self.assertEqual(recents_result, recents_stmt)
        self.assertEqual(favorites_result, favorites_stmt)


class SavedSearchesTestCase(unittest.TestCase):

    def setUp(self):
        self.dburi = "file:TESTING_MEMORY_DB?mode=memory&cache=shared"
        self.dbconn = util.LockableSqliteConnection(self.dburi)
        self.tablename = "testtable"
        self.testblasphemy = "BlasphemousGraphemesQwertyuiop"
        self.wordfilter = Wordfilter()
        self.wordfilter.add_words([self.testblasphemy])

        self.pairs = {
            'normal': ('something', 'not blasphemy'),
            'blasph': ('whatever', self.testblasphemy)}
        self.tuplepairs = {
            'normal': [self.pairs['normal']],
            'blasph': [self.pairs['normal'], self.pairs['blasph']]}

        # self.freespeech = munger.SavedSearches(self.dbconn, self.tablefreespeech, munger.ImpotentCensor())
        # self.censored = munger.SavedSearches(self.dbconn, self.tablecensored, Wordfilter())
        with self.dbconn as dbconn:
            dbconn.cursor.execute("CREATE TABLE {} (search, replace)".format(self.tablename))

    def tearDown(self):
        self.dbconn.close()

    def test_GET(self):
        ss = munger.SavedSearches(self.dbconn, self.tablename, munger.ImpotentCensor())
        result_empty = ss.GET()
        with self.dbconn as dbconn:
            dbconn.cursor.execute("INSERT INTO {} VALUES ('search one', 'replace one')".format(self.tablename))
            dbconn.cursor.execute("INSERT INTO {} VALUES ('search two', 'replace two')".format(self.tablename))
            dbconn.cursor.execute("INSERT INTO {} VALUES ('search tre', 'replace tre')".format(self.tablename))
        result_full = ss.GET()
        expected_full = json.loads("""[{"replace": "replace one", "search": "search one"}, {"replace": "replace two", "search": "search two"}, {"replace": "replace tre", "search": "search tre"}]""")
        self.assertEqual(result_empty, [])
        self.assertEqual(result_full, expected_full)

    def test_PUT_freespeech(self):
        ss = munger.SavedSearches(self.dbconn, self.tablename, munger.ImpotentCensor())
        ss.censor.add_words([self.testblasphemy])
        ss.PUT(self.pairs['blasph'][0], self.pairs['blasph'][1])
        ss.PUT(self.pairs['normal'][0], self.pairs['normal'][1])
        with self.dbconn as dbconn:
            dbconn.cursor.execute("SELECT * FROM {}".format(self.tablename))
            result = dbconn.cursor.fetchall()
        self.assertEqual(set(self.tuplepairs['blasph']), set(result))

    def test_PUT_censored(self):
        ss = munger.SavedSearches(self.dbconn, self.tablename, self.wordfilter)
        ss.PUT(self.pairs['normal'][0], self.pairs['normal'][1])
        with self.assertRaises(cherrypy.HTTPError):
            ss.PUT(self.pairs['blasph'][0], self.pairs['blasph'][1])
        with self.dbconn as dbconn:
            dbconn.cursor.execute("SELECT * FROM {}".format(self.tablename))
            result = dbconn.cursor.fetchall()
        self.assertEqual(self.tuplepairs['normal'], result)

    def test_PUT_readonly(self):
        ss = munger.SavedSearches(self.dbconn, self.tablename, munger.ImpotentCensor(), writeable=False)
        with self.assertRaises(cherrypy.HTTPError):
            ss.PUT(self.pairs['blasph'][0], self.pairs['blasph'][1])
        with self.assertRaises(cherrypy.HTTPError):
            ss.PUT(self.pairs['normal'][0], self.pairs['normal'][1])
        with self.dbconn as dbconn:
            dbconn.cursor.execute("SELECT * FROM {}".format(self.tablename))
            result = dbconn.cursor.fetchall()
        self.assertEqual(result, [])

    def test_addpair_freespeech(self):
        ss = munger.SavedSearches(self.dbconn, self.tablename, munger.ImpotentCensor())
        ss.addpair(self.pairs['normal'][0], self.pairs['normal'][1])
        ss.addpair(self.pairs['blasph'][0], self.pairs['blasph'][1])
        with self.dbconn as dbconn:
            dbconn.cursor.execute("SELECT * FROM {}".format(self.tablename))
            results = dbconn.cursor.fetchall()
        self.assertEqual(len(results), 2)
        self.assertIn(self.pairs['normal'], results)
        self.assertIn(self.pairs['blasph'], results)

    def test_addpair_censored(self):
        ss = munger.SavedSearches(self.dbconn, self.tablename, munger.ImpotentCensor(), writeable=False)
        ss.addpair(self.pairs['normal'][0], self.pairs['normal'][1])
        ss.addpair(self.pairs['blasph'][0], self.pairs['blasph'][1])
        with self.dbconn as dbconn:
            dbconn.cursor.execute("SELECT * FROM {}".format(self.tablename))
            results = dbconn.cursor.fetchall()
        self.assertEqual(len(results), 2)
        self.assertIn(self.pairs['normal'], results)
        self.assertIn(self.pairs['blasph'], results)

    def test_addpair_readonly(self):
        ss = munger.SavedSearches(self.dbconn, self.tablename, munger.ImpotentCensor(), writeable=False)
        ss.addpair(self.pairs['normal'][0], self.pairs['normal'][1])
        ss.addpair(self.pairs['blasph'][0], self.pairs['blasph'][1])
        with self.dbconn as dbconn:
            dbconn.cursor.execute("SELECT * FROM {}".format(self.tablename))
            results = dbconn.cursor.fetchall()
        self.assertEqual(set(self.tuplepairs['blasph']), set(results))


# class MiscellaneousTestCase(unittest.TestCase):

#     def test_recent_searches(self):
#         raise Exception("TODO: Add tests for how we add recent seraches")
