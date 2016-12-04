#!/usr/bin/env python3

# Run unit tests with "python -m unittest discover"

import io
import sqlite3
import unittest

import bible


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

    def _manual_setup_empty_db(self):
        dbconn = sqlite3.connect(':memory:')
        curse = dbconn.cursor()
        curse.execute(self.create_table_stmt)
        curse.close()
        return dbconn

    def _manual_setup_verses_db(self):
        dbconn = self._manual_setup_empty_db()
        curse = dbconn.cursor()
        for verse in self.testverses:
            curse.execute("INSERT INTO {} values (?, ?, ?, ?)".format(self.testtable), (verse.book, verse.chapter, verse.verse, verse.text))
        curse.close()
        return dbconn

    def test_bible_init_empty_db(self):
        dbconn = sqlite3.connect(':memory:')
        bible.Bible(dbconn, tablename=self.testtable)
        curse = dbconn.cursor()

        curse.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='{}'".format(self.testtable))
        passing = curse.fetchone()[0] == self.create_table_stmt

        dbconn.close()
        if not passing:
            raise Exception("New Bible object did not initialize its database")

    def test_bible_init_initialized_db(self):
        dbconn = self._manual_setup_empty_db()
        bible.Bible(dbconn, tablename=self.testtable)
        curse = dbconn.cursor()

        curse.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='{}'".format(self.testtable))
        passing = curse.fetchone()[0] == self.create_table_stmt

        dbconn.close()
        if not passing:
            raise Exception("New Bible object did not initialize its database")

    def test_bible_search(self):
        dbconn = self._manual_setup_verses_db()
        bib = bible.Bible(dbconn, tablename=self.testtable)

        verses = bib.search("TikTik")
        if len(verses) != 2:
            raise Exception("Expected 2 results but instead got {}".format(len(verses)))
        for verse in verses:
            if verse not in self.testverses:
                raise Exception("Verse '{}'' did not get represented properly".format(verse))
        dbconn.close()

    def test_bible_parsexml(self):
        parsedverses = bible.Bible.parsexml(io.StringIO(self.xmlbiblefragment))
        if parsedverses != self.testverses:
            raise Exception("Got different verses back out than I put in")

    def test_bible_addverses(self):
        dbconn = sqlite3.connect(':memory:')
        bib = bible.Bible(dbconn, tablename=self.testtable)
        bib.addverses(self.testverses)
        curse = dbconn.cursor()
        curse.execute("SELECT * FROM {}".format(self.testtable))
        verses = [bible.BibleVerse.fromtuple(v) for v in curse]
        dbconn.close()
        if verses != self.testverses:
            raise Exception("Got different verses back out than I put in")
