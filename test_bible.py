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
      <VERS vnumber="55">Nessie Mokele</VERS>
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
        print([str(v) for v in parsedverses])
        for tverse in self.testverses:
            found = False
            for pverse in parsedverses:
                print("Comparing:\n  {}\n  {}".format(pverse, tverse))
                if pverse == tverse:
                    found = True
                    break
            if not found:
                raise Exception("Expected to find {} in parsed verses but it wasn't there".format(tverse))

    def test_bible_addverses(self):
        raise Exception("UNIMPLEMENTED")

    # def test_bible_persistdb(self):
    #     bibletable = 'testkjv'
    #     bib = bible.Bible.fromxml(io.StringIO(biblefragment))
    #     dbconn = sqlite3.connect(':memory:')
    #     bib.persistdb(dbconn, bibletable)
    #     curse = dbconn.cursor()
    #     curse.execute("SELECT * FROM {}".format(bibletable))
    #     records = curse.fetchall()
    #     curse.close()
    #     dbconn.close()

    #     expected_len_records = 10
    #     expverse = bible.BibleVerse('Genesis', '1', '1', 'In the beginning God created the heaven and the earth.')
    #     if len(records) != expected_len_records:
    #         raise Exception("Expected to see {} recoreds but instead got {}".format(len(records), expected_len_records))
    #     verse = bible.BibleVerse.fromtuple(records[0])

    #     if verse != expverse:
    #         raise Exception("Expected the first record to expand to verse '{}' but was '{}' instead".format(expverse, verse))
