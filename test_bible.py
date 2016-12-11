#!/usr/bin/env python3

# Run unit tests with "python -m unittest discover"

import io
import sqlite3
import unittest

import bible
import util


class BibleTestCase(unittest.TestCase):

    testtable = 'testtable'
    create_table_stmt = "CREATE TABLE testtable (book, chapter, verse, text)"
    testverses = [
        bible.BibleVerse('RedBook', 11, 11, 'Tiktik Dragon'),
        bible.BibleVerse('BluBook', 22, 22, 'Dragon Beaman'),
        bible.BibleVerse('YelBook', 33, 33, 'Beaman Nessie'),
        bible.BibleVerse('PrpBook', 44, 44, 'Nessie Mokele'),
        bible.BibleVerse('GrnBook', 55, 55, 'Mokele Adjule'),
        bible.BibleVerse('OrgBook', 66, 66, 'Adjule Tiktik')]
    xmlbiblefragment = """<?xml version="1.0" encoding="utf-8"?>
<!--A random comment, whatever-->
<XMLBIBLE xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="zef2005.xsd" version="2.0.1.18" status="v" biblename="King James Version" type="x-bible" revision="0">
  <INFORMATION>
    <title>King James Version</title>
    <subject>The Holy Bible</subject>
  </INFORMATION>
  <BIBLEBOOK bnumber="1" bname="RedBook" bsname="Red">
    <CHAPTER cnumber="11">
      <VERS vnumber="11">Tiktik Dragon</VERS>
    </CHAPTER>
  </BIBLEBOOK>
  <BIBLEBOOK bnumber="2" bname="BluBook" bsname="Blu">
    <CHAPTER cnumber="22">
      <VERS vnumber="22">Dragon Beaman</VERS>
    </CHAPTER>
  </BIBLEBOOK>
  <BIBLEBOOK bnumber="3" bname="YelBook" bsname="Yel">
    <CHAPTER cnumber="33">
      <VERS vnumber="33">Beaman Nessie</VERS>
    </CHAPTER>
  </BIBLEBOOK>
  <BIBLEBOOK bnumber="4" bname="PrpBook" bsname="Prp">
    <CHAPTER cnumber="44">
      <VERS vnumber="44">Nessie Mokele</VERS>
    </CHAPTER>
  </BIBLEBOOK>
  <BIBLEBOOK bnumber="5" bname="GrnBook" bsname="Grn">
    <CHAPTER cnumber="55">
      <VERS vnumber="55">Mokele Adjule</VERS>
    </CHAPTER>
  </BIBLEBOOK>
  <BIBLEBOOK bnumber="6" bname="OrgBook" bsname="Org">
    <CHAPTER cnumber="66">
      <VERS vnumber="66">Adjule Tiktik</VERS>
    </CHAPTER>
  </BIBLEBOOK>
</XMLBIBLE>
"""

    def setUp(self):
        self.dburi = "file:TESTING_MEMORY_DB?mode=memory&cache=shared"
        self.dbconn = util.LockableSqliteConnection(self.dburi)
        self._bible = None

    def tearDown(self):
        self.dbconn.connection.close()
        self._bible = None

    @property
    def bible(self):
        """A bible.Bible object

        Intended to add it in the setUp() method, but using a lazily initialized property instead
        This way, our tests can control when to run the bible.Bible.__init__ code
        """
        if not self._bible:
            self._bible = bible.Bible(self.dbconn, tablename=self.testtable)
        return self._bible

    def test_bible_init_empty_db(self):
        self.bible
        with self.dbconn as dbconn:
            dbconn.cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='{}'".format(self.testtable))
            result = dbconn.cursor.fetchone()[0]
        self.assertEqual(result, self.create_table_stmt)

    def test_bible_init_initialized_db(self):
        with self.dbconn as dbconn:
            dbconn.cursor.execute(self.create_table_stmt)
        self.bible
        with self.dbconn as dbconn:
            dbconn.cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='{}'".format(self.testtable))
            result = dbconn.cursor.fetchone()[0]
        self.assertEqual(result, self.create_table_stmt)

    def test_bible_search(self):
        with self.dbconn as dbconn:
            dbconn.cursor.execute(self.create_table_stmt)
            for verse in self.testverses:
                dbconn.cursor.execute("INSERT INTO {} values (?, ?, ?, ?)".format(self.testtable), (verse.book, verse.chapter, verse.verse, verse.text))
        testverses = [self.testverses[0], self.testverses[-1]]
        verses = self.bible.search("TikTik")
        self.assertEqual(verses, testverses)

    def test_bible_parsexml(self):
        parsedverses = bible.Bible.parsexml(io.StringIO(self.xmlbiblefragment))
        self.assertEqual(parsedverses, self.testverses)

    def test_bible_addverses(self):
        self.bible.addverses(self.testverses)
        with self.dbconn as dbconn:
            dbconn.cursor.execute("SELECT * FROM {}".format(self.testtable))
            verses = [bible.BibleVerse.fromtuple(v) for v in dbconn.cursor]
        self.assertEqual(verses, self.testverses)
