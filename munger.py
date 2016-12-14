import json
import logging
import html
import os
import re
import sys

import cherrypy

scriptdir = os.path.dirname(os.path.realpath(__file__))
sys.path = [scriptdir] + sys.path

# Must come after updating sys.path because of WSGI
import bible  # noqa
import util   # noqa


cherrypy.tools.mako = cherrypy.Tool('on_start_resource', util.MakoLoader())


class ImpotentCensor(object):
    """A class which implements Wordfilter's blacklisted() method with one that always returns False"""

    def blacklisted(self, string):
        return False

    def add_words(self, stringArr):
        return


class SavedSearches(object):

    exposed = True

    def __init__(self, lockableconn, tablename, censor, writeable=True):
        self.connection = lockableconn
        self.tablename = tablename
        self.censor = censor
        self.writeable = writeable
        self.initialize_database()

    # def PUT(self, search, replace):
    #     if not self.writeable:
    #         raise cherrypy.HTTPError(403, "This service is read-only")
    #     elif self.censor.blacklisted(replace):
    #         raise cherrypy.HTTPError(451, "Content not appropriate")
    #     else:
    #         self.addpair(search, replace)

    def put(self, search, replace):
        if not self.writeable or self.censor.blacklisted(replace):
            return
        self.addpair(search, replace)

    @cherrypy.expose
    @cherrypy.tools.mako(filename="saved.mako")
    def GET(self):
        return {'pairs': self.get()}

    def get(self):
        with self.connection as dbconn:
            dbconn.cursor.execute("SELECT search, replace FROM {}".format(self.tablename))
            results = [{'search': r[0], 'replace': r[1]} for r in dbconn.cursor.fetchall()]
        return results

    def addpair(self, search, replace):
        """Add a pair, bypassing the censor and/or read-only flags"""
        esearch = html.escape(search)
        ereplace = html.escape(replace)
        with self.connection as dbconn:
            testsql = "SELECT search, replace FROM {} WHERE search=? AND replace=?".format(self.tablename)
            insertsql = "INSERT INTO {} VALUES (?, ?)".format(self.tablename)
            params = (esearch, ereplace)
            dbconn.cursor.execute(testsql, params)
            if dbconn.cursor.fetchall() == []:
                logging.debug("Pair '{}'/'{}' does not exist in '{}', adding...".format(esearch, ereplace, self.tablename))
                dbconn.cursor.execute(insertsql, params)
            else:
                logging.debug("Pair '{}'/'{}' already exists in '{}', nothing to do".format(esearch, ereplace, self.tablename))

    def initialize_database(self):
        with self.connection as dbconn:
            dbconn.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='{}'".format(self.tablename))
            if not dbconn.cursor.fetchone():
                dbconn.cursor.execute("CREATE TABLE {} (search, replace)".format(self.self.tablename))


class VersionApi(object):
    exposed = True

    def __init__(self, file=os.path.join(scriptdir, 'deploymentinfo.txt')):
        self.file = file
        self._version = None

    def GET(self):
        cherrypy.response.headers['Content-Type'] = "text/plain"
        if not self._version:
            try:
                with open(self.deploymentinfofile) as df:
                    self._version = df.read()
            except:
                self._version = "development version"
        return self.version


class BibleSearchApi(object):
    exposed = True

    def __init__(self, bible):
        self.bible = bible

    @cherrypy.popargs('search', 'replace')
    @cherrypy.tools.mako(filename='results.mako')
    def GET(self, search=None, replace=None, **posargs):
        if not search and replace:
            raise cherrypy.HTTPError(400, "u fukt up bad")
        return {'search': search, 'replace': replace, 'verses': self.get(search, replace)}

    def get(self, search, replace):
        # NOTE: Actual replacement is done in the template, not here
        return self.bible.search(search)


class SearchFormRerouter(object):
    """Redirect form data from /searchForm?search=SEARCH&replace=REPLACE to /SEARCH/REPLACE"""
    exposed = True

    def GET(self, search=None, replace=None):
        if not search or not replace:
            raise cherrypy.HTTPError(400, "Bad request")
        redirurl = "/{}/{}/".format(search, replace)
        raise cherrypy.HTTPRedirect(redirurl)


class Munger(object):
    exposed = True
    tablenames = {
        'recents': 'recent_searches',
        'favorites': 'favorite_searches'}

    def __init__(self, lockableconn, bible, censor):
        global scriptdir
        self._bible = bible
        self.censor = censor
        self.connection = lockableconn
        self.apptitle = "biblemunger"
        self.appsubtitle = "provocative text replacement in famous literature"
        self.filtering = False if censor is ImpotentCensor else True
        self.recents = SavedSearches(self.connection, self.tablenames['recents'], censor)
        self.favorites = SavedSearches(self.connection, self.tablenames['favorites'], censor, writeable=False)
        self.version = VersionApi()
        self.search = BibleSearchApi(bible)
        self.searchForm = SearchFormRerouter()

    @cherrypy.popargs('search', 'replace')
    @cherrypy.tools.mako(filename='munge.mako')
    def GET(self, search=None, replace=None, **posargs):
        pagetitle = self.apptitle
        exreplacement = None
        results = None
        if search and replace:
            self.recents.put(search, replace)
            results = self.search.get(search, replace)
            logging.debug("Search/replace: {}/{}".format(search, replace))
            pagetitle = "{}: {} ⇒ {}".format(self.apptitle, search, replace)
            # TODO: put a method for finding the shortest verse matching a search on the bible object?
            verses = self._bible.search(search)
            if len(verses) > 0:
                shortestresult = min([v.text for v in verses], key=len)
                exreplacement = re.sub(search, replace, shortestresult)
                logging.debug("Found a verse! Example replacement: {}".format(exreplacement))
        return {
            'pagetitle':      pagetitle,
            'apptitle':       self.apptitle,
            'appsubtitle':    self.appsubtitle,
            'exreplacement':  exreplacement,
            'recents':        self.recents.get(),
            'favorites':      self.favorites.get(),
            'search':         search,
            'replace':        replace,
            'results':        results,
            'filterinuse':    self.filtering}


def application(environ=None, start_response=None):
    """Webserver setup code

    If 'environ' and 'start_response' parameters are passed, assume WSGI.

    Otherwise, start cherrypy's built-in webserver.
    """

    global scriptdir

    mode = 'wsgi' if environ and start_response else 'cherrypy'

    configfile = os.path.join(scriptdir, 'biblemunger.config.json')
    with open(configfile) as f:
        configuration = json.load(f)

    if not configuration['loglevel'] or configuration['loglevel'] == "INFO":
        loglevel = logging.INFO
    elif configuration['loglevel'] == "DEBUG":
        loglevel = logging.DEBUG
    else:
        raise Exception("Log level '{}' is not supported".format(configuration['loglevel']))
    if configuration['logfile']:
        logfile = os.path.abspath(configuration['logfile'])
        logging.basicConfig(filename=logfile, level=loglevel)
    else:
        logging.basicConfig(level=loglevel)

    logging.debug("Using config file at {}".format(configfile))

    if os.name == 'nt':
        dburitemplate = "file:///{}?cache=shared"
    else:
        dburitemplate = "file:///{}?cache=shared"
    dburi = dburitemplate.format(os.path.abspath(configuration['dbpath']))
    logging.debug("Using SQLite URI: {}".format(dburi))

    lockableconn = util.LockableSqliteConnection(dburi)

    bib = bible.Bible(lockableconn)
    if not bib.initialized:
        bib.addversesfromxml(os.path.abspath(configuration['bible']))

    if configuration['wordfilter']:
        from wordfilter import Wordfilter
        censor = Wordfilter()
        filtering = True
    else:
        censor = ImpotentCensor()
        filtering = False
    logging.debug("Enabling censorship: {}".format(filtering))

    if mode == 'wsgi':
        sys.stdout = sys.stderr
        cherrypy.config.update({'environment': 'embedded'})
    elif mode == 'cherrypy':
        cherrypy.config.update({
            'server.socket_port': configuration['port'],
            'server.socket_host': configuration['server']})

    server = Munger(lockableconn, bib, censor)
    for fave in configuration['favorites']:
        server.favorites.addpair(fave['search'], fave['replace'])

    cherrypy.tree.mount(server, '/', {
        '/': {
            'request.dispatch': cherrypy.dispatch.MethodDispatcher(),
            'tools.mako.directories': os.path.join(scriptdir, 'temple'),
            'tools.staticdir.root': scriptdir},
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'static'},
        "/favicon.ico": {
            "tools.staticfile.on": True,
            "tools.staticfile.filename": os.path.join(scriptdir, 'static', 'favicon.ico')}})

    if mode == 'wsgi':
        return cherrypy.tree(environ, start_response)
    elif mode == 'cherrypy':
        cherrypy.engine.signals.subscribe()
        cherrypy.engine.start()
        cherrypy.engine.block()
