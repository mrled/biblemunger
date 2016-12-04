import re
import xml.etree.ElementTree as ET


class BibleVerse(object):

    def __init__(self, book, chapter, verse, text, markedup=None):
        self.book = book
        self.chapter = chapter
        self.verse = verse
        self.text = text
        self.markedup = markedup if markedup else text

    @classmethod
    def fromtuple(cls, tup):
        return BibleVerse(tup[0], tup[1], tup[2], tup[3])

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self.__dict__ == other.__dict__
        return NotImplemented

    def __ne__(self, other):
        if isinstance(other, self.__class__):
            return not self == other
        return NotImplemented

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
                    verses += [BibleVerse(book.get('bname'), chapter.get('cnumber'), verse.get('vnumber'), verse.text)]
        return Bible(verses)

    @classmethod
    def fromdb(cls, dbconn, tablename):
        curse = dbconn.cursor()
        curse.execute("SELECT book, chapter, verse, text FROM {}".format(tablename))
        rows = curse.fetchall()
        verses = []
        for row in rows:
            verses += [BibleVerse.fromtuple(row)]
        return Bible(verses)

    def persistdb(self, dbconn, tablename):
        curse = dbconn.cursor()
        curse.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='{}'".format(tablename))
        if not curse.fetchone():
            curse.execute("CREATE TABLE {} (book, chapter, verse, text)".format(tablename))
            dbconn.commit()
        for verse in self.verses:
            curse.execute("INSERT INTO {} values (?, ?, ?, ?)".format(tablename), (verse.book, verse.chapter, verse.verse, verse.text))
        dbconn.commit()

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
            munged += [BibleVerse(verse.book, verse.chapter, verse.verse, plaintext, markedup=markedtext)]
        return munged
