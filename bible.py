import re
import xml.etree.ElementTree as ET


class BibleVerse(object):

    def __init__(self, text, verse, chapter, book):
        # TODO: refactor so we don't pass a tuple here, that's confusing
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
        return "{} {}:{}: {}".format(self.book, self.chapter, self.verse, self.text)


class Bible(object):

    def __init__(self, file):
        self.xmletree = ET.parse(file)

        def findelems(base, tag):
            return (child for child in base if child.tag == tag)

        self.verses = []
        for book in findelems(self.xmletree.getroot(), 'BIBLEBOOK'):
            for chapter in findelems(book, 'CHAPTER'):
                for verse in findelems(chapter, 'VERS'):
                    self.verses += [BibleVerse(verse.text, verse.get('vnumber'), chapter.get('cnumber'), book.get('bname'))]

    def search(self, string):
        verses = []
        for verse in self.verses:
            if re.search(string, verse.text):
                verses += [verse]
        return verses

    def replace(self, old, new):
        munged = []
        for verse in self.search(old):
            f = re.IGNORECASE
            plaintext = re.sub(old, new, verse.text, flags=f)
            markedtext = re.sub(old, '*****{}******'.format(new), verse.text, flags=f)
            munged += [BibleVerse(
                (plaintext, markedtext),
                verse.verse, verse.chapter, verse.book)]
        return munged
