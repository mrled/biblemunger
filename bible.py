import re
import xml.etree.ElementTree as ET


class BibleVerse(object):

    def __init__(self, book, chapter, verse, text, markedup=None):
        self.book = book
        self.chapter = int(chapter)
        self.verse = int(verse)
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
        return "{} {}:{} {}".format(self.book, self.chapter, self.verse, self.text)


class Bible(object):

    def __init__(self, lockableconn, tablename='bible'):
        self.tablename = tablename
        self.connection = lockableconn
        with self.connection as dbconn:
            dbconn.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='{}'".format(self.tablename))
            if not dbconn.cursor.fetchone():
                dbconn.cursor.execute("CREATE TABLE {} (book, chapter, verse, text)".format(self.tablename))

    @classmethod
    def parsexml(cls, file):
        def findelems(base, tagname):
            return (child for child in base if child.tag == tagname)
        xmletree = ET.parse(file)
        verses = []
        for book in findelems(xmletree.getroot(), 'BIBLEBOOK'):
            for chapter in findelems(book, 'CHAPTER'):
                for verse in findelems(chapter, 'VERS'):
                    verses += [BibleVerse(book.get('bname'), chapter.get('cnumber'), verse.get('vnumber'), verse.text)]
        return verses

    @property
    def initialized(self):
        with self.connection as dbconn:
            dbconn.cursor.execute("SELECT verse FROM {} LIMIT 1".format(self.tablename))
            result = dbconn.cursor.fetchone()
        return result is not None

    def addverses(self, verses):
        with self.connection as dbconn:
            for verse in verses:
                dbconn.cursor.execute("INSERT INTO {} values (?, ?, ?, ?)".format(self.tablename), (verse.book, verse.chapter, verse.verse, verse.text))

    def addversesfromxml(self, file):
        self.addverses(Bible.parsexml(file))

    def search(self, search):
        sql = "SELECT book, chapter, verse, text FROM {} WHERE text LIKE ?".format(self.tablename)
        params = ("%{}%".format(search), )
        verses = []
        with self.connection as dbconn:
            dbconn.cursor.execute(sql, params)
            for result in dbconn.cursor:
                verses += [BibleVerse.fromtuple(result)]
        return verses

    def replace(self, old, new):
        results = self.search(old)
        for verse in results:
            f = re.IGNORECASE
            verse.text = re.sub(old, new, verse.text, flags=f)
            verse.markedup = re.sub(old, '*****{}******'.format(new), verse.text, flags=f)
        return results
