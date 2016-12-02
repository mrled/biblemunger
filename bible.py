import re
import xml.etree.ElementTree as ET


class BibleVerse(object):

    def __init__(self, text, verse, chapter, book, markedup=None):
        self.text = text
        self.markedup = markedup if markedup else text
        self.verse = verse
        self.chapter = chapter
        self.book = book

    def __str__(self):
        return "{} {}:{}: {}".format(self.book, self.chapter, self.verse, self.text)


class Bible(object):

    def __init__(self, verses):
        self.verses = verses

    @classmethod
    def fromxml(cls, file):
        def findelems(base, tagname):
            return (child for child in base if child.tag == tagname)
        xmletree = ET.parse(file)
        verses = []
        for book in findelems(xmletree.getroot(), 'BIBLEBOOK'):
            for chapter in findelems(book, 'CHAPTER'):
                for verse in findelems(chapter, 'VERS'):
                    verses += [BibleVerse(verse.text, verse.get('vnumber'), chapter.get('cnumber'), book.get('bname'))]
        return Bible(verses)

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
            munged += [BibleVerse(plaintext, verse.verse, verse.chapter, verse.book, markedup=markedtext)]
        return munged
