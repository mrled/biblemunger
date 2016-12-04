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

    def __init__(self, dbconn, tablename='bible'):
        self.tablename = tablename
        self.connection = dbconn

        curse = self.connection.cursor()
        curse.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='{}'".format(self.tablename))
        if not curse.fetchone():
            curse.execute("CREATE TABLE {} (book, chapter, verse, text)".format(self.tablename))
            self.connection.commit()
        curse.close()

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

    def addverses(self, verses):
        curse = self.connection.cursor()
        for verse in verses:
            curse.execute("INSERT INTO {} values (?, ?, ?, ?)".format(self.tablename), (verse.book, verse.chapter, verse.verse, verse.text))
        self.connection.commit()
        curse.close()

    def addversesfromxml(self, file):
        self.addverses(Bible.parsexml(file))

    def search(self, search):
        curse = self.connection.cursor()
        sql = "SELECT book, chapter, verse, text FROM {} WHERE text LIKE ?".format(self.tablename)
        params = ("%{}%".format(search), )
        curse.execute(sql, params)
        verses = []
        for result in curse:
            verses += [BibleVerse.fromtuple(result)]
        curse.close()
        return verses

    def replace(self, old, new):
        results = self.search(old)
        for verse in results:
            f = re.IGNORECASE
            verse.text = re.sub(old, new, verse.text, flags=f)
            verse.markedup = re.sub(old, '*****{}******'.format(new), verse.text, flags=f)
        return results
