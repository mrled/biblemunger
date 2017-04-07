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

versionfile = os.path.join(scriptdir, 'deploymentinfo.txt')
cherrypy.tools.mako = cherrypy.Tool('on_start_resource', util.MakoLoader())
log = logging.getLogger(__name__)
log.addHandler(logging.NullHandler())


class ImpotentCensor(object):
    """A Wordfilter-compatible object that never censors anything"""

    def blacklisted(self, string):
        return False

    def add_words(self, stringArr):
        return


class SavedSearches():
    """A database-backed list of saved searches"""

    def __init__(self, lockableconn, tablename, censor):
        self.connection = lockableconn
        self.censor = censor
        self.tablename = tablename

    def initialize_table(self, initialize):
        if initialize is util.InitializationOption.NoAction:
            return
        with self.connection.rw as dbconn:
            if initialize is util.InitializationOption.Reinitialize:
                dbconn.cursor.execute("DROP TABLE IF EXISTS {}".format(self.tablename))
                dbconn.connection.commit()
            dbconn.cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='{}'".format(self.tablename))
            if not dbconn.cursor.fetchone():
                dbconn.cursor.execute("CREATE TABLE {} (search, replace)".format(self.tablename))

    def add(self, search, replace, force=False):
        """Add a search/replace pair"""
        if not force and self.censor.blacklisted(replace):
            return
        esearch = html.escape(search)
        ereplace = html.escape(replace)

        with self.connection.ro as dbconn:
            dbconn.cursor.execute(
                "SELECT search, replace FROM {} WHERE search=? AND replace=?".format(self.tablename),
                (esearch, ereplace))
            present = dbconn.cursor.fetchall()
        if present:
            log.debug("Pair '{}'/'{}' already exists in '{}', nothing to do".format(esearch, ereplace, self.tablename))
        else:
            log.debug("Pair '{}'/'{}' does not exist in '{}', adding...".format(esearch, ereplace, self.tablename))
            with self.connection.rw as dbconn:
                dbconn.cursor.execute(
                    "INSERT INTO {} VALUES (?, ?)".format(self.tablename),
                    (esearch, ereplace))

    def get(self):
        with self.connection.ro as dbconn:
            dbconn.cursor.execute("SELECT search, replace FROM {}".format(self.tablename))
            results = [{'search': r[0], 'replace': r[1]} for r in dbconn.cursor.fetchall()]
        return results


class MungerVersion():
    """A way to get the deployment version"""

    def __init__(self, versionfile):
        self.versionfile = versionfile

    def get(self):
        if not self._version:
            try:
                with open(self.versionfile) as df:
                    self._version = df.read()
            except:
                self._version = "development version"
        return self.version


class Munger():
    """Provocative text replacement in famous literature"""

    def __init__(self, bible, recents, favorites, mungerversion):
        self.bible = bible
        self.apptitle = "biblemunger"
        self.appsubtitle = "provocative text replacement in famous literature"
        self.filtering = recents.censor is not ImpotentCensor
        self._version = None
        self._recents = recents
        self._favorites = favorites
        self._version = mungerversion

    @cherrypy.expose
    def index(self, *args, **posargs):
        raise cherrypy.HTTPRedirect('munge')

    @cherrypy.expose
    @cherrypy.popargs('start', 'end')
    @cherrypy.tools.mako(filename='passage.html.mako')
    def passage(self, start=None, end=None, **posargs):
        if not start:
            raise cherrypy.HTTPError(400, "Bad request")
        return {
            'pagetitle':      "{} &em; {}".format(start, end),
            'apptitle':       self.apptitle,
            'appsubtitle':    self.appsubtitle,
            'recents':        self._recents.get(),
            'favorites':      self._favorites.get(),
            'start':          start,
            'end':            end,
            'filterinuse':    self.filtering}

    @cherrypy.expose
    @cherrypy.popargs('search', 'replace')
    @cherrypy.tools.mako(filename='munge.html.mako')
    def munge(self, search=None, replace=None, **posargs):
        pagetitle = self.apptitle
        exreplacement = None
        results = None
        if search and replace:
            log.debug("Search/replace: {}/{}".format(search, replace))
            results = self.bible.search(search)
            self._recents.add(search, replace)
            pagetitle = "{}: {} ⇒ {}".format(self.apptitle, search, replace)
            if len(results) > 0:
                shortestresult = min([v.text for v in results], key=len)
                exreplacement = re.sub(search, replace, shortestresult)
                log.debug("Found a verse! Example replacement: {}".format(exreplacement))
        return {
            'pagetitle':      pagetitle,
            'apptitle':       self.apptitle,
            'appsubtitle':    self.appsubtitle,
            'exreplacement':  exreplacement,
            'recents':        self._recents.get(),
            'favorites':      self._favorites.get(),
            'search':         search,
            'replace':        replace,
            'results':        results,
            'filterinuse':    self.filtering}

    @cherrypy.expose
    @cherrypy.tools.mako(filename="saved.html.mako")
    def recents(self):
        return {'pairs': self._recents.get()}

    @cherrypy.expose
    @cherrypy.tools.mako(filename="saved.html.mako")
    def favorites(self):
        return {'pairs': self._favorites.get()}

    @cherrypy.expose
    def version(self):
        cherrypy.response.headers['Content-Type'] = "text/plain"
        return self._version.get()

    @cherrypy.expose
    @cherrypy.popargs('search', 'replace')
    @cherrypy.tools.mako(filename='results.html.mako')
    def search(self, search=None, replace=None, **posargs):
        if not search and replace:
            raise cherrypy.HTTPError(400, "Both 'search' and 'replace' arguments are required")
        if (search, replace) not in self._favorites.get():
            self._recents.add(search, replace)
        # Note: the actual replacement is done in the template itself
        return {'search': search, 'replace': replace, 'verses': self.bible.search(search)}

    @cherrypy.expose
    @cherrypy.popargs('search', 'replace')
    def searchForm(self, search=None, replace=None):
        """Redirect form data from /searchForm?search=SEARCH&replace=REPLACE to /SEARCH/REPLACE"""
        if not search or not replace:
            raise cherrypy.HTTPError(400, "Bad request")
        redirurl = "/{}/{}/".format(search, replace)
        raise cherrypy.HTTPRedirect(redirurl)


def configure():
    """Read configuration from the filesystem, and process it for use in my application"""

    configs = [
        os.path.join(scriptdir, 'biblemunger.config.default.json'),
        os.path.join(scriptdir, 'biblemunger.config.json')]
    configuration = {}
    for config in configs:
        try:
            with open(config) as f:
                c = json.load(f)
            configuration.update(c)
            log.debug("Found config file at {}".format(config))
        except:
            pass
    if not configuration:
        raise Exception("No configuration file was found")

    configuration['dbpath'] = os.path.abspath(configuration['dbpath'])

    if configuration['debug']:
        configuration['loglevel'] = logging.DEBUG
    else:
        configuration['loglevel'] = logging.INFO
    configuration['logformatter'] = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    configuration['loghandlers'] = [logging.StreamHandler(stream=sys.stdout)]
    if configuration['logfile']:
        configuration['logfile'] = os.path.abspath(configuration['logfile'])
        configuration['loghandlers'] += [logging.FileHandler(configuration['logfile'])]
    for handler in configuration['loghandlers']:
        handler.setFormatter(configuration['logformatter'])

    if configuration['wordfilter']:
        from wordfilter import Wordfilter
        configuration['censor'] = Wordfilter()
    else:
        configuration['censor'] = ImpotentCensor()

    configuration['dburi'] = "file:///{}?cache=shared".format(configuration['dbpath'])

    return configuration


def application(environ=None,
                start_response=None,
                configuration=configure(),
                initialize=util.InitializationOption.NoAction):
    """Webserver setup code

    environ: passed from WSGI (if not present, use cherrypy's built-in webserver)
    start_response: passed from WSGI (if not present, use cherrypy's built-in webserver)
    configuration: a configuration object, normally from the configure() function
    initialize: controls db initialization. See util.InitializationOption

    If 'environ' and 'start_response' parameters are passed, assume WSGI; otherwise, start cherrypy's built-in webserver.
    """

    log.setLevel(configuration['loglevel'])
    for handler in configuration['loghandlers']:
        log.addHandler(handler)
    log.debug("BibleMunger logging configured")

    lockableconn = util.LockableSqliteConnection(configuration['dburi'])
    log.debug("Using SQLite URI: {}".format(configuration['dburi']))

    bib = bible.Bible(lockableconn, configuration['tablenames']['bible'])
    bib.initialize_table(initialize)
    if not bib.hasverses:
        log.debug("Bible doesn't have its database initialized; initializing...")
        bib.addversesfromxml(os.path.abspath(configuration['bible']))

    log.debug("Enabling censorship: {}".format(configuration['wordfilter']))

    # Recent searches use the censor:
    recents = SavedSearches(
        lockableconn,
        configuration['tablenames']['recents'],
        configuration['censor'])
    recents.initialize_table(initialize)

    # Favorite searches bypass the censor (b/c they're admin-controlled anyway)
    favorites = SavedSearches(
        lockableconn,
        configuration['tablenames']['favorites'],
        ImpotentCensor())
    favorites.initialize_table(initialize)
    for fave in configuration['favorites']:
        favorites.add(fave['search'], fave['replace'], force=True)

    global versionfile
    vers = MungerVersion(versionfile)

    server = Munger(bib, recents, favorites, vers)

    cherrypy.tree.mount(server, '/', {
        '/': {
            'tools.mako.directories': os.path.join(scriptdir, 'temple'),
            'tools.mako.debug': configuration['debug'],
            'tools.staticdir.root': scriptdir},
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'static'},
        "/favicon.ico": {
            "tools.staticfile.on": True,
            "tools.staticfile.filename": os.path.join(scriptdir, 'static', 'favicon.ico')}})

    mode = 'wsgi' if environ and start_response else 'cherrypy'
    if mode == 'wsgi':
        log.debug("Returning BibleMunger as WSGI application")
        sys.stdout = sys.stderr
        cherrypy.config.update({'environment': 'embedded'})
        return cherrypy.tree(environ, start_response)
    elif mode == 'cherrypy':
        log.debug("Starting BibleMunger's CherryPy HTTP server")
        cherrypy.config.update({
            'server.socket_port': configuration['port'],
            'server.socket_host': configuration['server']})
        cherrypy.engine.signals.subscribe()
        cherrypy.engine.start()
        cherrypy.engine.block()
