#!/usr/bin/env python

# Got a Bible from here:
# http://sourceforge.net/projects/zefania-sharp/files/Bibles/ENG/King%20James/King%20James%20Version/SF_2009-01-23_ENG_KJV_%28KING%20JAMES%20VERSION%29.zip/download

# probably offer cli mode (at first)
# and then HTTP mode (later on) using the http.server modile in python3

import xml.etree.ElementTree as ET
import re
import argparse
import sys
from pdb import set_trace as strace

import cherrypy
from mako.template import Template

class BibleVerse(object):
    def __init__(self, text, verse, chapter, book):
        self.text = text
        self.verse = verse
        self.chapter = chapter
        self.book = book
    def __str__(self):
        string = "{} {}:{}: {}".format(
            self.book, self.chapter, self.verse, self.text)
        return string
    def htmltr(self):
        html = "<tr><td><strong>{} {}:{}</strong></td><td>{}</td>".format(
            self.book, self.chapter, self.verse, self.text)
        return html

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
            #if verse.text.find(string):
            #    found += verse
            if re.search(string, verse.text):
                found += [verse]
        return found

    def replace(self, old, new):
        '''
        some of my favorites:
        - hearts, feels
        - servant, uber driver
        - the saints, my waifu
        - exile, otaku
        '''
        munged = []
        for verse in self.search(old):
            munged += [BibleVerse(
                re.sub(old, new, verse.text, flags=re.IGNORECASE),
                verse.verse, verse.chapter, verse.book)]
        return munged

index_template_text = """
<html><head><title>${pagetitle}</title></head>
<body><center>
<h2><a href="/">${apptitle}</a></h2>
<p>Find some text in the Bible and replace it with other text.</p>
<p>(Based on <a href="http://the-toast.net/tag/bible-verses/">some excellence</a> by Mallory Ortberg. XML KJV from <a href="http://sourceforge.net/projects/zefania-sharp/files/Bibles/ENG/King%20James/King%20James%20Version/SF_2009-01-23_ENG_KJV_%28KING%20JAMES%20VERSION%29.zip/download">the Zefania project</a>.)</p>
%if favorites:
  <p>Can't think of anything to search for? Try these:
  <ul style="list-style:none;">
    %for fav in favorites:
      <li><a href="/?search=${fav['search']}&replace=${fav['replace']}">${fav['search']} &rArr; ${fav['replace']}</a></li>
    %endfor
  </ul></p>
%endif
<form method=GET action="/">
<table border=0 cellpadding=5 cellspacing=5><tr>
<td valign="TOP">Search: <input type=text name="search" size=20></td>
<td valign="TOP">Replace: <input type=text name="replace" size=20></td>
<td valign="TOP"><input type=submit value="Munge"></td>
</tr>
</table>
</form>
%if queried:
  %if results:
    <h2>${resultstitle}</h2>
    <table border=0 cellspacing=5 cellpadding=5 width="540" align="CENTER">
    %for verse in results:
      ${verse.htmltr()}
    %endfor
    </table>
  %else:
    <h2>${title}</h2>
    <p>None</p>
  %endif
%endif     
</center></body></html>
"""
index_template = Template(index_template_text)
class BibleMungingServer(object):
    def __init__(self):
        self.bible = Bible('./kjv.xml')

    @cherrypy.expose
    def index(self, search=None, replace=None):
        apptitle = "fuck with the holy scriptures"
        pagetitle = apptitle
        queried = False
        resultstitle = None
        results = None
        
        if search and replace:
            resultstitle = "cat kjv | sed s/{}/{}/g".format(search, replace)
            pagetitle = resultstitle
            results = self.bible.replace(search, replace)
            queried = True

        favorites = [
            {'search':'hearts', 'replace':'feels'},
            {'search':'servant', 'replace':'uber driver'},
            {'search':'exile', 'replace':'otaku'},
            {'search':'the saints', 'replace':'my waifu'}]

        return index_template.render(
            pagetitle = pagetitle,
            apptitle = apptitle,
            queried = queried,
            resultstitle = resultstitle,
            results = results,
            favorites = favorites)

def main(*args, **kwargs):
    parser = argparse.ArgumentParser(
        description='Fuck with the Bible')
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

    bible = Bible('./kjv.xml')

    parsed = parser.parse_args()
    if parsed.web:
        cherrypy.config.update({
            'server.socket_port': 8187,
            'server.socket_host': '0.0.0.0'})

        cherrypy.quickstart(BibleMungingServer())
    if parsed.search:
        for verse in bible.search(parsed.search):
            print(verse)
    if parsed.replace:
        for verse in bible.replace( parsed.replace[0], parsed.replace[1] ):
            print(verse)

if __name__ == '__main__':
    sys.exit(main(*sys.argv))

