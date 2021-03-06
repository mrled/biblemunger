import argparse
import json
import logging
import html
import os
import re
import sys

import cherrypy

SCRIPTDIR = os.path.dirname(os.path.realpath(__file__))
sys.path = [SCRIPTDIR] + sys.path

# Must come after updating sys.path because of WSGI
import bible  # noqa
import util   # noqa

VERSIONFILE = os.path.join(SCRIPTDIR, 'deploymentinfo.txt')
cherrypy.tools.mako = cherrypy.Tool('on_start_resource', util.MakoLoader())
LOGGER = logging.getLogger('biblemunger')
LOGGER.addHandler(logging.NullHandler())


class SavedSearches():
    """A database-backed list of saved searches
    """

    def __init__(self, lockableconn, tablename):
        self.connection = lockableconn
        self.tablename = tablename

    def initialize_table(self, initialize):
        if initialize is util.InitializationOption.NoAction:
            return
        with self.connection.rw as dbconn:
            if initialize is util.InitializationOption.Reinitialize:
                dbconn.cursor.execute("DROP TABLE IF EXISTS {}".format(self.tablename))
                dbconn.connection.commit()
            dbconn.cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='{}'".format(
                    self.tablename))
            if not dbconn.cursor.fetchone():
                dbconn.cursor.execute("CREATE TABLE {} (search, replace)".format(self.tablename))

    def add(self, search, replace):
        """Add a search/replace pair
        """
        esearch = html.escape(search)
        ereplace = html.escape(replace)

        with self.connection.ro as dbconn:
            dbconn.cursor.execute(
                "SELECT search, replace FROM {} WHERE search=? AND replace=?".format(
                    self.tablename),
                (esearch, ereplace))
            present = dbconn.cursor.fetchall()
        if present:
            LOGGER.debug(
                "Pair '{}'/'{}' already exists in '{}', nothing to do".format(
                    esearch, ereplace, self.tablename))
        else:
            LOGGER.debug(
                "Pair '{}'/'{}' does not exist in '{}', adding...".format(
                    esearch, ereplace, self.tablename))
            with self.connection.rw as dbconn:
                dbconn.cursor.execute(
                    "INSERT INTO {} VALUES (?, ?)".format(self.tablename),
                    (esearch, ereplace))

    def get(self):
        with self.connection.ro as dbconn:
            dbconn.cursor.execute(
                "SELECT search, replace FROM {} ORDER BY search".format(self.tablename))
            results = [{'search': r[0], 'replace': r[1]} for r in dbconn.cursor.fetchall()]
        return results


class MungerVersion():
    """A way to get the deployment version
    """

    def __init__(self, VERSIONFILE):
        self.VERSIONFILE = VERSIONFILE

    def get(self):
        if not self._version:
            try:
                with open(self.VERSIONFILE) as df:
                    self._version = df.read()
            except:
                self._version = "development version"
        return self.version


class Munger():
    """Provocative text replacement in famous literature
    """

    def __init__(self, bible, favorites, mungerversion):
        self.bible = bible
        self.apptitle = "biblemunger"
        self.appsubtitle = "provocative text replacement in famous literature"
        self._version = None
        self._favorites = favorites
        self._version = mungerversion

    @cherrypy.expose
    def index(self, *args, **posargs):
        raise cherrypy.HTTPRedirect('munge')

    @cherrypy.expose
    @cherrypy.popargs('start', 'end')
    @cherrypy.tools.mako(filename='passage.html.mako')
    def passage(self, vidrange="", **posargs):
        """Return a contiguous list of verses

        vidrange:   A range of verses, specified by verse id ("vid") and separated by a colon
                    For example: "startvid:endvid"
                    The vids are specified like "Genesis-1-1"
                    The startvid is required. The endvid is optional; if it's not present, just show
                    a single verse
        """
        split = vidrange.split(":")
        if len(split) < 1 or len(split) < 1 or len(split[0]) == 0:
            raise cherrypy.HTTPError(
                400,
                "Bad request: 'vidrange' parameter must be in form 'Genesis-1-1:Genesis-2-1'")
        start = split[0]
        end = split[1] if len(split) == 2 else None
        if end:
            vrangelabel = "{} - {}".format(start, end)
        else:
            vrangelabel = start

        verses = self.bible.passage(start, endvid=end)

        return {
            'pagetitle':      vrangelabel,
            'apptitle':       self.apptitle,
            'appsubtitle':    self.appsubtitle,
            'favorites':      self._favorites.get(),
            'vrangelabel':    vrangelabel,
            'verses':         verses,
            'start':          start,
            'end':            end}

    @cherrypy.expose
    @cherrypy.popargs('search', 'replace')
    @cherrypy.tools.mako(filename='munge.html.mako')
    def munge(self, search=None, replace=None, **posargs):
        pagetitle = self.apptitle
        exreplacement = None
        results = None
        if search and replace:
            LOGGER.debug("Search/replace: {}/{}".format(search, replace))
            results = self.bible.search(search)
            pagetitle = "{}: {} ⇒ {}".format(self.apptitle, search, replace)
            if len(results) > 0:
                shortestresult = min([v.text for v in results], key=len)
                exreplacement = re.sub(search, replace, shortestresult)
                LOGGER.debug("Found a verse! Example replacement: {}".format(exreplacement))
        return {
            'pagetitle':      pagetitle,
            'apptitle':       self.apptitle,
            'appsubtitle':    self.appsubtitle,
            'exreplacement':  exreplacement,
            'favorites':      self._favorites.get(),
            'search':         search,
            'replace':        replace,
            'results':        results}

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
        # Note: the actual replacement is done in the template itself
        return {'search': search, 'replace': replace, 'verses': self.bible.search(search)}

    @cherrypy.expose
    @cherrypy.popargs('search', 'replace')
    def searchForm(self, search=None, replace=None):
        """Redirect form data from /searchForm?search=SEARCH&replace=REPLACE to /SEARCH/REPLACE
        """
        if not search or not replace:
            raise cherrypy.HTTPError(400, "Bad request")
        redirurl = "/{}/{}/".format(search, replace)
        raise cherrypy.HTTPRedirect(redirurl)


def rel_resolve(path):
    """Resolve a path that might be relative to this script
    """
    if os.path.isabs(path):
        return os.path.abspath(path)
    else:
        return os.path.join(SCRIPTDIR, path)


def configure():
    """Read configuration from the filesystem, and process it for use in my application
    """

    configs = [
        os.path.join(SCRIPTDIR, 'biblemunger.config.default.json'),
        os.path.join(SCRIPTDIR, 'biblemunger.config.json')]
    configuration = {}
    for config in configs:
        try:
            with open(config) as f:
                c = json.load(f)
            configuration.update(c)
            LOGGER.debug("Found config file at {}".format(config))
        except:
            pass
    if not configuration:
        raise Exception("No configuration file was found")

    configuration['dbpath'] = rel_resolve(configuration['dbpath'])
    configuration['bible'] = rel_resolve(configuration['bible'])
    configuration['logfile'] = rel_resolve(configuration['logfile'])

    if configuration['debug']:
        configuration['loglevel'] = logging.DEBUG
    else:
        configuration['loglevel'] = logging.INFO
    configuration['logformatter'] = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    configuration['loghandlers'] = [logging.StreamHandler(stream=sys.stdout)]
    if configuration['logfile']:
        configuration['logfile'] = os.path.abspath(configuration['logfile'])
        configuration['loghandlers'] += [logging.FileHandler(configuration['logfile'])]
    for handler in configuration['loghandlers']:
        handler.setFormatter(configuration['logformatter'])

    configuration['dburi'] = "file://{}?cache=shared".format(configuration['dbpath'])

    return configuration


def init(
        configuration=configure(),
        initialize=util.InitializationOption.NoAction):
    """Webserver setup code

    configuration: a configuration object, normally from the configure() function
    initialize: controls db initialization. See util.InitializationOption
    """

    cp_logger = logging.getLogger('cherrypy')
    cp_logger.setLevel(configuration['loglevel'])
    LOGGER.setLevel(configuration['loglevel'])
    for handler in configuration['loghandlers']:
        LOGGER.addHandler(handler)
    LOGGER.debug("BibleMunger logging configured")

    lockableconn = util.LockableSqliteConnection(configuration['dburi'])
    LOGGER.debug("Using SQLite URI: {}".format(configuration['dburi']))

    bib = bible.Bible(lockableconn, configuration['tablenames']['bible'])
    bib.initialize_table(initialize)
    if not bib.hasverses:
        LOGGER.debug("Bible doesn't have its database initialized; initializing...")
        bib.addversesfromxml(os.path.abspath(configuration['bible']))

    favorites = SavedSearches(lockableconn, configuration['tablenames']['favorites'])
    favorites.initialize_table(initialize)
    for fave in configuration['favorites']:
        favorites.add(fave['search'], fave['replace'])

    vers = MungerVersion(VERSIONFILE)

    server = Munger(bib, favorites, vers)
    cp_root_config = {
        '/': {
            'tools.mako.directories': os.path.join(SCRIPTDIR, 'temple'),
            'tools.mako.debug': configuration['debug'],
            'tools.staticdir.root': SCRIPTDIR,
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'static',
        },
        "/favicon.ico": {
            "tools.staticfile.on": True,
            "tools.staticfile.filename": os.path.join(SCRIPTDIR, 'static', 'favicon.ico'),
        },
    }

    return (server, cp_root_config)


def start_cherrypy(server, cp_root_config, host, port):
    """Start the CherryPy internal webserver
    """
    LOGGER.debug("Starting BibleMunger's CherryPy HTTP server")
    cherrypy.config.update({
        'server.socket_host': host,
        'server.socket_port': port,
    })
    cherrypy.tree.mount(server, '/', cp_root_config)
    cherrypy.engine.signals.subscribe()
    cherrypy.engine.start()
    cherrypy.engine.block()


def parseargs():
    """Parse commandline arguments
    """
    parser = argparse.ArgumentParser(description="Provocative text replacement with famous literature")
    parser.add_argument(
        '--initialize', '-i',
        default=util.InitializationOption.NoAction, type=util.InitializationOption.fromstr,
        help=" ".join([
            'Controls whether the database is assumed in a good state,'
            'initialized assuming empty state, or dropped then initialized']))
    parsed = parser.parse_args()

    return parsed


parsed = parseargs()
configuration = configure()
server, cp_root_config = init(configuration=configuration, initialize=parsed.initialize)
if __name__ == '__main__':
    # If we're being run directly, use the CherryPy webserver
    start_cherrypy(server, cp_root_config, configuration['server'], configuration['port'])
elif __name__.startswith('_mod_wsgi_'):
    # If we're not being run directly, configure for WSGI
    sys.stdout = sys.stderr  # Useful for logging WSGI applications
    cherrypy.config.update({'environment': 'embedded'})
    configuration = configure()
    application = cherrypy.Application(
        server,
        script_name=None,
        config=cp_root_config)
