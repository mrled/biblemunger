import unittest

import bible
import munger
import util


class BibleMungingServerTestCase(unittest.TestCase):

    def setUp(self):
        self.dburi = "file:TESTING_MEMORY_DB?mode=memory&cache=shared"
        self.dbconn = util.LockableSqliteConnection(self.dburi)
        self.bible = bible.Bible(self.dbconn)

    def tearDown(self):
        self.dbconn.connection.close()

    def test_object_init_nofilter(self):
        apptitle = "test app title"
        appsubtitle = "test app subtitle"
        faves = [
            {'search': 'search one', 'replace': 'replace one'},
            {'search': 'search two', 'replace': 'replace two'},
            {'search': 'search tre', 'replace': 'replace tre'}]
        bms = munger.BibleMungingServer(self.dbconn, self.bible, faves, apptitle, appsubtitle, wordfilter=False)
        self.assertEqual(faves, bms.favorite_searches)
        self.assertEqual(apptitle, bms.apptitle)
        self.assertEqual(appsubtitle, bms.appsubtitle)
        self.assertNotIn('add_words', dir(bms.wordfilter))

    def test_object_init_filter(self):
        testword = 'QwertyStringUsedForTestingZxcvb'
        bms = munger.BibleMungingServer(self.dbconn, self.bible, [], "apptitle", "appsubtitle", wordfilter=True)
        self.assertIn('add_words', dir(bms.wordfilter))
        self.assertFalse(bms.wordfilter.blacklisted(testword))
        bms.wordfilter.add_words([testword])
        self.assertTrue(bms.wordfilter.blacklisted(testword))

    def test_initialize_database(self):
        create_table_stmt = "CREATE TABLE recent_searches (search, replace)"
        bms = munger.BibleMungingServer(self.dbconn, self.bible, [], "app title", "app subtitle", wordfilter=False)
        bms.initialize_database()
        recents_tablename = bms.tablenames['recents']
        with self.dbconn as dbconn:
            dbconn.cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='{}'".format(recents_tablename))
            result = dbconn.cursor.fetchone()
        self.assertEqual(result[0], create_table_stmt)

    def test_recent_searches(self):
        bms = munger.BibleMungingServer(self.dbconn, self.bible, [], "app title", "app subtitle", wordfilter=False)
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
