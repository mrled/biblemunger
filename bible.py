import xml.etree.ElementTree as ET

import util


class BibleVerse(object):
    """A verse in the holiest of fuckin Scriptures

    Parameters:
    book: The name of the book, such as "Genesis"
    chapter: The number of the chapter, such as "1"
    verse: The number of the verse, such as "1"
    text: The text of the verse, such as "In the beginning, ..."

    Other properties:
    vid: A verse identifier, such as "Genesis-1-1"; this must be unique to this verse, and is used to find it in the database
    """

    def __init__(self, book, chapter, verse, text):
        self.book = book
        self.chapter = int(chapter)
        self.verse = int(verse)
        self.text = text
        self.vid = "{}-{}-{}".format(self.book, self.chapter, self.verse)

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
        with self.connection.rw as dbconn:
            dbconn.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='{}'".format(self.tablename))
            createsql = util.normalizewhitespace("""CREATE TABLE {} (
                ordinal INTEGER PRIMARY KEY ASC,
                vid TEXT,
                book TEXT,
                chapter INTEGER,
                verse INTEGER,
                text TEXT
            )
            """.format(self.tablename))
            if not dbconn.cursor.fetchone():
                dbconn.cursor.execute(createsql)

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
        """Return True if at least one verse is present; return False otherwise"""
        with self.connection.ro as dbconn:
            dbconn.cursor.execute("SELECT verse FROM {} LIMIT 1".format(self.tablename))
            result = dbconn.cursor.fetchone()
        return result is not None

    def addverses(self, verses):
        with self.connection.rw as dbconn:
            for verse in verses:
                sql = "INSERT INTO {} (vid, book, chapter, verse, text) values (?, ?, ?, ?, ?)".format(self.tablename)
                params = (verse.vid, verse.book, verse.chapter, verse.verse, verse.text)
                dbconn.cursor.execute(sql, params)

    def addversesfromxml(self, file):
        self.addverses(Bible.parsexml(file))

    def search(self, search):
        sql = "SELECT book, chapter, verse, text FROM {} WHERE text LIKE ?".format(self.tablename)
        params = ("%{}%".format(search), )
        verses = []
        with self.connection.ro as dbconn:
            dbconn.cursor.execute("PRAGMA case_sensitive_like = ON;")
            dbconn.cursor.execute(sql, params)
            for result in dbconn.cursor:
                verses += [BibleVerse(*result)]
        return verses

    def passage(self, startvid, endvid=None):
        """Return a single verse (if only startvid is provided) or a range between two verses (if an endvid is provided also)

        startvid: a verse identifier representing the start of the passage
        endvid: a verse identifier representing the end of the passage
        """

        verses = []
        with self.connection.ro as dbconn:
            ordinalsql = "SELECT ordinal FROM {} WHERE vid=?".format(self.tablename)
            dbconn.cursor.execute(ordinalsql, (startvid, ))
            startordinal = dbconn.cursor.fetchone()[0]

            if not endvid:
                searchsql = "SELECT book, chapter, verse, text FROM {} WHERE ordinal = ?".format(self.tablename)
                searchparams = (startordinal, )
            else:
                dbconn.cursor.execute(ordinalsql, (endvid, ))
                endordinal = dbconn.cursor.fetchone()[0]
                if endordinal <= startordinal:
                    raise Exception("Invalid passage: endvid comes before startvid")
                searchsql = "SELECT book, chapter, verse, text FROM {} WHERE ordinal >= ? AND ordinal < ?".format(self.tablename)
                searchparams = (startordinal, endordinal)

            dbconn.cursor.execute(searchsql, searchparams)
            for result in dbconn.cursor:
                verses += [BibleVerse(*result)]

        return verses
