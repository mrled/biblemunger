import json
import unittest

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

    def tearDown(self):
        self.dbconn.close()

    def test_initialize_database(self):
        ss = munger.SavedSearches(self.dbconn, self.tablename)
        create_stmt = "CREATE TABLE {} (search, replace)".format(self.tablename)
        ss.initialize_table(util.InitializationOption.InitIfNone)
        with self.dbconn.ro as dbconn:
            dbconn.cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='{}'".format(self.tablename))
            sql_result = dbconn.cursor.fetchone()[0]
        self.assertEqual(sql_result, create_stmt)

    def test_get(self):
        ss = munger.SavedSearches(self.dbconn, self.tablename)
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

    def test_add(self):
        ss = munger.SavedSearches(self.dbconn, self.tablename)
        ss.initialize_table(util.InitializationOption.InitIfNone)
        pairs = [('testSearchOne', 'testReplaceOne'), ('testSearchTwo', 'testReplaceTwo')]
        ss.add(*pairs[0])
        ss.add(*pairs[1])
        with self.dbconn.ro as dbconn:
            dbconn.cursor.execute("SELECT * FROM {}".format(self.tablename))
            result = dbconn.cursor.fetchall()
        self.assertEqual(set(pairs), set(result))

# class MungerVersionTestCase(unittest.TestCase):

#     def test_get(self):
#         raise Exception("TODO: Add test for MungerVersion class")
