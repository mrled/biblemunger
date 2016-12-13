import configparser
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
        self.writeable = bool(writeable)

    @cherrypy.tools.json_out()
    def GET(self):
        with self.connection as dbconn:
            dbconn.cursor.execute("SELECT search, replace FROM {}".format(self.tablename))
            results = [{'search': r[0], 'replace': r[1]} for r in dbconn.cursor.fetchall()]
        return results or []

    def PUT(self, search, replace):
        if not self.writeable:
            raise cherrypy.HTTPError(403, "This service is read-only")
        elif self.censor.blacklisted(replace):
            raise cherrypy.HTTPError(451, "Content not appropriate")
        else:
            self.addpair(search, replace)

    def addpair(self, search, replace):
        with self.connection as dbconn:
            testsql = "SELECT search, replace FROM {} WHERE search=? AND replace=?".format(self.tablename)
            insertsql = "INSERT INTO {} VALUES (?, ?)".format(self.tablename)
            params = (search, replace)
            dbconn.cursor.execute(testsql, params)
            if dbconn.cursor.fetchall() == []:
                dbconn.cursor.execute(insertsql, params)


class VersionApi(object):
    exposed = True

    def GET(self):
        cherrypy.response.headers['Content-Type'] = "text/plain"
        deploymentinfofile = os.path.join(scriptdir, 'deploymentinfo.txt')
        try:
            with open(deploymentinfofile) as df:
                deploymentinfo = df.read()
        except:
            deploymentinfo = "development version"
        return deploymentinfo


class BibleSearchApi(object):
    exposed = True
    dictencoder = util.DictEncoder()

    def __init__(self, bible):
        self.bible = bible

    @cherrypy.expose
    @cherrypy.tools.json_out(handler=dictencoder.cherrypy_json_handler)
    def GET(self, search):
        return self.bible.search(search)


class ApiServer(object):

    exposed = True
    tablenames = {
        'recents': 'recent_searches',
        'favorites': 'favorite_searches'}

    def __init__(self, lockableconn, bible, censor):

        global scriptdir

        self.connection = lockableconn
        self.initialize_database()

        self.recents = SavedSearches(self.connection, self.tablenames['recents'], censor)
        self.favorites = SavedSearches(self.connection, self.tablenames['favorites'], censor, writeable=False)
        self.version = VersionApi()
        self.search = BibleSearchApi(bible)

    def initialize_database(self):
        with self.connection as dbconn:
            dbconn.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='{}'".format(self.tablenames['recents']))
            if not dbconn.cursor.fetchone():
                dbconn.cursor.execute("CREATE TABLE {} (search, replace)".format(self.tablenames['recents']))
            dbconn.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='{}'".format(self.tablenames['favorites']))
            if not dbconn.cursor.fetchone():
                dbconn.cursor.execute("CREATE TABLE {} (search, replace)".format(self.tablenames['favorites']))

    def GET(self):
        cherrypy.response.headers['Content-Type'] = "text/plain"
        return "Welcome to the BibleMunger API"


class FrontEndServer(object):

    def __init__(self, lockableconn, bible, filtering=False):

        global scriptdir

        self._bible = bible
        self.connection = lockableconn
        self.filtering = filtering
        self.apptitle = "biblemunger"
        self.appsubtitle = "provocative text replacement in famous literature"

    @cherrypy.expose
    @cherrypy.tools.mako(filename='munge.mako')
    def index(self, search=None, replace=None):
        if search and replace:
            pagetitle = "{}: {} ⇒ {}".format(self.apptitle, search, replace)
            # TODO: put a method for finding the shortest verse matching a search on the bible object?
            verses = self._bible.search(search)
            if len(verses) > 0:
                shortestresult = min(verses, key=len)
                exreplacement = re.sub(search, replace, shortestresult)
        else:
            pagetitle = self.apptitle
            exreplacement = None
        return {
            'pagetitle':      pagetitle,
            'apptitle':       self.apptitle,
            'appsubtitle':    self.appsubtitle,
            'exreplacement':  exreplacement,
            'filterinuse':    self.filtering}


def configure():
    """Get biblemunger configuration

    NOTE: It's not currently possible to define more than 1 favorite replacement set with the same search term
    That is, if you put "search = replace1" and "search = replace2" in the config file, only the second will come through

    TODO: allow definition of multiple replacement sets with the same search term
    """

    global scriptdir

    # The first of these, the default config file, must exist (and is in git)
    # The second is an optional config file that can be provided by the user
    # NOTE: We want the config files to work even for WSGI, so we can't use a command line parameter for the user's config
    defaultconfig = os.path.join(scriptdir, 'biblemunger.config.default')
    userconfig = os.path.join(scriptdir, 'biblemunger.config')

    configuration = configparser.ConfigParser()
    configuration.readfp(open(defaultconfig))
    if os.path.exists(userconfig):
        configuration.readfp(open(userconfig))

    return configuration


def application(environ=None, start_response=None):
    """Webserver setup code

    If 'environ' and 'start_response' parameters are passed, assume WSGI.

    Otherwise, start cherrypy's built-in webserver.
    """

    global scriptdir

    mode = 'wsgi' if environ and start_response else 'cherrypy'

    configuration = configure()
    dburi = "file://{}?cache=shared".format(os.path.abspath(configuration.get('biblemunger', 'dbpath')))
    lockableconn = util.LockableSqliteConnection(dburi)

    bib = bible.Bible(lockableconn)
    if not bib.initialized:
        bib.addversesfromxml(os.path.abspath(configuration.get('biblemunger', 'bible')))

    if configuration.getboolean('biblemunger', 'wordfilter'):
        from wordfilter import Wordfilter
        censor = Wordfilter()
        filtering = True
    else:
        censor = ImpotentCensor()
        filtering = False

    if mode == 'wsgi':
        sys.stdout = sys.stderr
        cherrypy.config.update({'environment': 'embedded'})
    elif mode == 'cherrypy':
        cherrypy.config.update({
            'server.socket_port': int(configuration.get('biblemunger', 'port')),
            'server.socket_host': configuration.get('biblemunger', 'server')})

    frontend = FrontEndServer(lockableconn, bib, filtering=filtering)
    api = ApiServer(lockableconn, bib, censor)

    cherrypy.tree.mount(frontend, '/', {
        '/': {
            'tools.mako.directories': os.path.join(scriptdir, 'temple'),
            'tools.staticdir.root': scriptdir},
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'static'},
        "/favicon.ico": {
            "tools.staticfile.on": True,
            "tools.staticfile.filename": os.path.join(scriptdir, 'static', 'favicon.ico')}})
    cherrypy.tree.mount(api, '/api', {
        '/': {'request.dispatch': cherrypy.dispatch.MethodDispatcher()}})

    if mode == 'wsgi':
        return cherrypy.tree(environ, start_response)
    elif mode == 'cherrypy':
        cherrypy.engine.signals.subscribe()
        cherrypy.engine.start()
        cherrypy.engine.block()
