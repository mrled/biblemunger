import json
import unittest

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
        self.dbconn.connection.close()

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
        self.tablefreespeech = "freespeech"
        self.tablecensored = "censored"
        self.testblasphemy = "BlasphemousGraphemesQwertyuiop"
        self.freespeech = munger.SavedSearches(self.dbconn, self.tablefreespeech, munger.ImpotentCensor())
        self.censored = munger.SavedSearches(self.dbconn, self.tablecensored, Wordfilter())
        with self.dbconn as dbconn:
            dbconn.cursor.execute("CREATE TABLE {} (search, replace)".format(self.tablefreespeech))
            dbconn.cursor.execute("CREATE TABLE {} (search, replace)".format(self.tablecensored))

    def tearDown(self):
        self.dbconn.connection.close()

    def test_GET(self):
        result_empty = self.freespeech.GET()
        with self.dbconn as dbconn:
            dbconn.cursor.execute("INSERT INTO {} VALUES ('search one', 'replace one')".format(self.tablefreespeech))
            dbconn.cursor.execute("INSERT INTO {} VALUES ('search two', 'replace two')".format(self.tablefreespeech))
            dbconn.cursor.execute("INSERT INTO {} VALUES ('search tre', 'replace tre')".format(self.tablefreespeech))
        result_full = self.freespeech.GET()
        expected_full = json.loads("""[{"replace": "replace one", "search": "search one"}, {"replace": "replace two", "search": "search two"}, {"replace": "replace tre", "search": "search tre"}]""")
        self.assertEqual(result_empty, [])
        self.assertEqual(result_full, expected_full)

    def test_PUT_freespeech(self):
        self.freespeech.censor.add_words([self.testblasphemy])
        self.freespeech.PUT('something', self.testblasphemy)
        self.freespeech.PUT('something2', 'not blasphemy')
        result_freespeech = self.freespeech.GET()
        expected_freespeech = '[{"search": "something", "replace": "%s"}, {"search": "something2", "replace": "not blasphemy"}]' % self.testblasphemy
        self.assertEqual(result_freespeech, expected_freespeech)

    def test_PUT_censored(self):
        self.censored.censor.add_words([self.testblasphemy])
        self.censored.PUT('something', self.testblasphemy)
        self.censored.PUT('something2', 'not blasphemy')
        result_censored = self.censored.GET()
        expected_censored = '[{"search": "something2", "replace": "not blasphemy"}]'
        self.assertEqual(result_censored, expected_censored)


# class MiscellaneousTestCase(unittest.TestCase):

#     def test_recent_searches(self):
#         raise Exception("TODO: Add tests for how we add recent seraches")
