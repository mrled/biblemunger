import json
import unittest

from wordfilter import Wordfilter

# import bible
import munger
import util


# class FrontEndServerTestCase(unittest.TestCase):

#     def test_munge_page(self):
#         raise Exception("TODO: implement test_munge_page")


# class MungerTestCase(unittest.TestCase):

#     def test_something(self):
#         raise Exception("Do I need to test this class? idek")


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

    def tearDown(self):
        self.dbconn.close()

    def test_initialize_database(self):
        ss = munger.SavedSearches(self.dbconn, self.tablename, munger.ImpotentCensor())
        create_stmt = "CREATE TABLE {} (search, replace)".format(self.tablename)
        ss.initialize_table(util.InitializationOption.InitIfNone)
        with self.dbconn.ro as dbconn:
            dbconn.cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='{}'".format(self.tablename))
            recents_result = dbconn.cursor.fetchone()[0]
        self.assertEqual(recents_result, create_stmt)

    def test_get(self):
        ss = munger.SavedSearches(self.dbconn, self.tablename, munger.ImpotentCensor())
        ss.initialize_table(util.InitializationOption.InitIfNone)
        result_empty = ss.get()
        with self.dbconn.rw as dbconn:
            dbconn.cursor.execute("INSERT INTO {} VALUES ('search one', 'replace one')".format(self.tablename))
            dbconn.cursor.execute("INSERT INTO {} VALUES ('search two', 'replace two')".format(self.tablename))
            dbconn.cursor.execute("INSERT INTO {} VALUES ('search tre', 'replace tre')".format(self.tablename))
        result_full = ss.get()
        expected_full = json.loads("""[{"replace": "replace one", "search": "search one"}, {"replace": "replace two", "search": "search two"}, {"replace": "replace tre", "search": "search tre"}]""")
        self.assertEqual(result_empty, [])
        self.assertEqual(result_full, expected_full)

    def test_add_freespeech(self):
        ss = munger.SavedSearches(self.dbconn, self.tablename, munger.ImpotentCensor())
        ss.initialize_table(util.InitializationOption.InitIfNone)
        ss.censor.add_words([self.testblasphemy])
        ss.add(self.pairs['blasph'][0], self.pairs['blasph'][1])
        ss.add(self.pairs['normal'][0], self.pairs['normal'][1])
        with self.dbconn.ro as dbconn:
            dbconn.cursor.execute("SELECT * FROM {}".format(self.tablename))
            result = dbconn.cursor.fetchall()
        self.assertEqual(set(self.tuplepairs['blasph']), set(result))

    def test_add_censored(self):
        ss = munger.SavedSearches(self.dbconn, self.tablename, self.wordfilter)
        ss.initialize_table(util.InitializationOption.InitIfNone)
        ss.add(self.pairs['normal'][0], self.pairs['normal'][1])
        ss.add(self.pairs['blasph'][0], self.pairs['blasph'][1])
        with self.dbconn.ro as dbconn:
            dbconn.cursor.execute("SELECT * FROM {}".format(self.tablename))
            result = dbconn.cursor.fetchall()
        self.assertEqual(self.tuplepairs['normal'], result)


# class MungerVersionTestCase(unittest.TestCase):

#     def test_get(self):
#         raise Exception("TODO: Add test for MungerVersion class")
