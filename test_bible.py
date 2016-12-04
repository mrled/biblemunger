#!/usr/bin/env python3

# Run unit tests with "python -m unittest discover"

import io
import sqlite3
import unittest

import bible


biblefragment = """<?xml version="1.0" encoding="utf-8"?>
<!--Visit the online documentation for Zefania XML Markup-->
<!--http://bgfdb.de/zefaniaxml/bml/-->
<!--Download another Zefania XML files from-->
<!--http://sourceforge.net/projects/zefania-sharp-->
<XMLBIBLE xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:noNamespaceSchemaLocation="zef2005.xsd" version="2.0.1.18" status="v" biblename="King James Version" type="x-bible" revision="0">
  <INFORMATION>
    <title>King James Version</title>
    <creator>
    </creator>
    <subject>The Holy Bible</subject>
    <description>In 1604, King James I of England authorized that a new translation of the Bible into English be started. It was finished in 1611, just 85 years after the first translation of the New Testament into English appeared (Tyndale, 1526). The Authorized Version, or King James Version, quickly became the standard for English-speaking Protestants. Its flowing language and prose rhythm has had a profound influence on the literature of the past 300 years.</description>
    <publisher>FREE BIBLE SOFTWARE GROUP</publisher>
    <contributors />
    <date>2009-01-23</date>
    <type>Bible</type>
    <format>Zefania XML Bible Markup Language</format>
    <identifier>KJV</identifier>
    <source>http://www.unboundbible.com/zips/index.cfm?lang=English</source>
    <language>ENG</language>
    <coverage>provide the Bible to the nations of the world</coverage>
    <rights>
    </rights>
  </INFORMATION>
  <BIBLEBOOK bnumber="1" bname="Genesis" bsname="Gen">
    <CHAPTER cnumber="1">
      <VERS vnumber="1">In the beginning God created the heaven and the earth.</VERS>
      <VERS vnumber="2">And the earth was without form, and void; and darkness was upon the face of the deep. And the Spirit of God moved upon the face of the waters.</VERS>
      <VERS vnumber="3">And God said, Let there be light: and there was light.</VERS>
      <VERS vnumber="4">And God saw the light, that it was good: and God divided the light from the darkness.</VERS>
      <VERS vnumber="5">And God called the light Day, and the darkness he called Night. And the evening and the morning were the first day.</VERS>
      <VERS vnumber="6">And God said, Let there be a firmament in the midst of the waters, and let it divide the waters from the waters.</VERS>
      <VERS vnumber="7">And God made the firmament, and divided the waters which were under the firmament from the waters which were above the firmament: and it was so.</VERS>
      <VERS vnumber="8">And God called the firmament Heaven. And the evening and the morning were the second day.</VERS>
      <VERS vnumber="9">And God said, Let the waters under the heaven be gathered together unto one place, and let the dry land appear: and it was so.</VERS>
      <VERS vnumber="10">And God called the dry land Earth; and the gathering together of the waters called he Seas: and God saw that it was good.</VERS>
    </CHAPTER>
  </BIBLEBOOK>
</XMLBIBLE>
"""


class BibleTestCase(unittest.TestCase):

    def test_bible_fromxml(self):
        bib = bible.Bible.fromxml(io.StringIO(biblefragment))

        results_God = bib.search("God")
        expected_len_results_God = 10
        if len(results_God) != expected_len_results_God:
            raise Exception("Expected to see {} results but instead got {}".format(expected_len_results_God, len(results_God)))
        expected_results0_God = 'In the beginning God created the heaven and the earth.'
        if results_God[0].text != expected_results0_God:
            raise Exception("Expected to see the first result as '{}' but was '{}'".format(expected_results0_God, results_God[0].text))

        results_god = bib.search("god")
        expected_len_results_god = 10
        if len(results_God) != expected_len_results_god:
            raise Exception("Expected to see {} results but instead got {}".format(expected_len_results_god, len(results_god)))

    def test_bible_persistdb(self):
        bibletable = 'testkjv'
        bib = bible.Bible.fromxml(io.StringIO(biblefragment))
        dbconn = sqlite3.connect(':memory:')
        bib.persistdb(dbconn, bibletable)
        curse = dbconn.cursor()
        curse.execute("SELECT * FROM {}".format(bibletable))
        records = curse.fetchall()
        curse.close()
        dbconn.close()

        expected_len_records = 10
        expverse = bible.BibleVerse('Genesis', '1', '1', 'In the beginning God created the heaven and the earth.')
        if len(records) != expected_len_records:
            raise Exception("Expected to see {} recoreds but instead got {}".format(len(records), expected_len_records))
        verse = bible.BibleVerse.fromtuple(records[0])

        if verse != expverse:
            raise Exception("Expected the first record to expand to verse '{}' but was '{}' instead".format(expverse, verse))

    def test_bible_fromdb(self):
        bibletable = 'testkjv'
        dbconn = sqlite3.connect(':memory:')
        curse = dbconn.cursor()
        curse.execute("CREATE TABLE {} (book, chapter, verse, text)".format(bibletable))
        dbconn.commit()
        verses = [
            bible.BibleVerse('YellowBook', 11, 11, 'YellowBook 11:11 Verse Text'),
            bible.BibleVerse('OrangeBook', 12, 18, 'OrangeBook 12:18 Verse Text'),
            bible.BibleVerse('PurpleBook', 22, 47, 'PurpleBook 22:47 Verse Text')]
        for verse in verses:
            curse.execute("INSERT INTO {} values (?, ?, ?, ?)".format(bibletable), (verse.book, verse.chapter, verse.verse, verse.text))
        dbconn.commit()

        bib = bible.Bible.fromdb(dbconn, bibletable)
        for idx in range(len(verses)):
            if bib.verses[idx] != verses[idx]:
                raise Exception("Expected record at index {} to expand to verse '{}' but was '{}' instead".format(idx, verses[idx], bib.verses[idx]))
