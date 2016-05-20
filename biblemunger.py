#!/usr/bin/env python3

import argparse
import configparser
import os
import re
import sys
import xml.etree.ElementTree as ET
#from pdb import set_trace as strace


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


def resolvepath(path, relativeto):
    if os.path.isabs(path):
        return path
    elif not relativeto:
        # Assume relative to CWD
        return os.path.join(os.getcwd(), path)
    else:
        return os.path.join(relativeto, path)


def configure():
    scriptdir = os.path.dirname(os.path.realpath(__file__))

    # The first of these, the default config file, must exist (and is in git)
    # The second is an optional config file that can be provided by the user
    # NOTE: We want the config files to work even for WSGI, so we can't use a
    #       command line parameter for the user's config
    defaultconfig = os.path.join(scriptdir, 'biblemunger.config.default')
    userconfig = os.path.join(scriptdir, 'biblemunger.config')

    configuration = configparser.ConfigParser()
    configuration.readfp(open(defaultconfig))
    if os.path.exists(userconfig):
        configuration.readfp(open(userconfig))

    configuration['bmweb']['dbpath'] = resolvepath(
        configuration['bmweb']['dbpath'], scriptdir)
    configuration['biblemunger']['bible'] = resolvepath(
        configuration['biblemunger']['bible'], scriptdir)

    return configuration


def main(*args, **kwargs):
    configuration = configure()
    appsubtitle = configuration.get('biblemunger', 'appsubtitle')
    bible = Bible(configuration.get('biblemunger', 'bible'))

    parser = argparse.ArgumentParser(
        description=appsubtitle)
    actiong = parser.add_mutually_exclusive_group()
    actiong.add_argument(
        '--search', '-s', action='store',
        help='Search for a string')
    actiong.add_argument(
        '--replace', '-r', nargs=2, action='store',
        help='Replace one string with another')
    actiong.add_argument(
        '--web', '-w', action='store_true',
        help='Run a webserver')

    parsed = parser.parse_args()
    if parsed.web:
        import bmweb
        bmweb.run(configuration)
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
