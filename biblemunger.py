#!/usr/bin/env python

import argparse
import os
import re
import sys
import xml.etree.ElementTree as ET

apptitle = "biblemunger"
appsubtitle = "fuck with the holy scriptures"
scriptroot = os.path.dirname(os.path.realpath(__file__))
kjvpath = os.path.join(scriptroot, "kjv.xml")


def strace():
    from pdb import set_trace
    set_trace()


class BibleVerse(object):

    def __init__(self, text, verse, chapter, book):
        if type(text) is tuple:
            self.text = text[0]
            self.text_markedup = text[1]
        else:
            self.text = text
            self.text_markedup = text
        self.verse = verse
        self.chapter = chapter
        self.book = book

    def __str__(self):
        string = "{} {}:{}: {}".format(
            self.book, self.chapter, self.verse, self.text)
        return string


class Bible(object):

    def __init__(self, file):
        self.xmletree = ET.parse(file)

        def find_books():
            books = []
            for child in self.xmletree.getroot():
                if child.tag == "BIBLEBOOK":
                    books += [child]
            return books

        def find_chapters(book):
            chapters = []
            for child in book:
                if child.tag == "CHAPTER":
                    chapters += [child]
            return chapters

        def find_verses(chapter):
            verses = []
            for child in chapter:
                if child.tag == "VERS":
                    verses += [child]
            return verses

        self.verses = []
        for book in find_books():
            bname = book.get('bname')
            for chapter in find_chapters(book):
                cnum = chapter.get('cnumber')
                for verse in find_verses(chapter):
                    self.verses += [BibleVerse(
                        verse.text, verse.get('vnumber'), cnum, bname)]

    def search(self, string):
        found = []
        for verse in self.verses:
            if re.search(string, verse.text):
                found += [verse]
        return found

    def replace(self, old, new):
        munged = []
        for verse in self.search(old):
            f = re.IGNORECASE
            plaintext = re.sub(old, new, verse.text, flags=f)
            markedtext = re.sub(
                #old, '<span class="munged">{}</span>'.format(new), verse.text,
                old, '*****{}******'.format(new), verse.text,
                flags=f)
            munged += [BibleVerse(
                (plaintext, markedtext),
                verse.verse, verse.chapter, verse.book)]
        return munged


def main(*args, **kwargs):
    global appsubtitle
    parser = argparse.ArgumentParser(
        description=appsubtitle)
    actiong = parser.add_mutually_exclusive_group()
    actiong.add_argument(
        '--search', '-s', action='store',
        help='Search for a string')
    actiong.add_argument(
        '--replace', '-r', nargs=2, action='store',
        help='Replace one string with another')
    # actiong.add_argument(
    #     '--web', '-w', action='store', dest='webconfig', nargs='?',
    #     help='Run a webserver, optionally specifying a config file')
    actiong.add_argument(
        '--web', '-w', action='store_true',
        help='Run a webserver')

    bible = Bible(kjvpath)

    parsed = parser.parse_args()
    if parsed.web:
        import bmweb
        bmweb.starthttp()
    elif parsed.search:
        for verse in bible.search(parsed.search):
            print(verse)
    elif parsed.replace:
        for verse in bible.replace(parsed.replace[0], parsed.replace[1]):
            print(verse)
    else:
        print(parser.format_help())
        sys.exit()

if __name__ == '__main__':
    sys.exit(main(*sys.argv))
