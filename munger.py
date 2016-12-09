import configparser
import json
import os
import sqlite3
import sys
import threading
# from pdb import set_trace as strace

import cherrypy
from mako.lookup import TemplateLookup

scriptdir = os.path.dirname(os.path.realpath(__file__))

try:
    import bible
except:
    # Necessary because of WSGI; must be done before importing any modules in this directory
    sys.path = [scriptdir] + sys.path
    import bible


class MakoHandler(cherrypy.dispatch.LateParamPageHandler):
    """Callable which sets response.body"""

    def __init__(self, template, next_handler):
        self.template = template
        self.next_handler = next_handler

    def __call__(self):
        env = globals().copy()
        env.update(self.next_handler())
        return self.template.render(**env)


class MakoLoader(object):

    def __init__(self):
        self.lookups = {}

    def __call__(self, filename, directories, module_directory=None, collection_size=-1):
        # Find the appropriate template lookup.
        key = (tuple(directories), module_directory)
        try:
            lookup = self.lookups[key]
        except KeyError:
            lookup = TemplateLookup(directories=directories, module_directory=module_directory, collection_size=collection_size)
            self.lookups[key] = lookup
        cherrypy.request.lookup = lookup

        # Replace the current handler.
        cherrypy.request.template = lookup.get_template(filename)
        cherrypy.request.handler = MakoHandler(cherrypy.request.template, cherrypy.request.handler)


cherrypy.tools.mako = cherrypy.Tool('on_start_resource', MakoLoader())


class DictEncoder(json.JSONEncoder):
    """JSON encoder for any object that can be encoded just by getting to its underlying .__dict__ attribute"""

    def default(self, obj):
        return obj.__dict__

    # def iterencode(self, value):
    #     for chunk in super().iterencode(value):
    #         yield chunk.encode("utf-8")

    def json_handler(self, *args, **kwargs):
        """A handler for use with CherryPy

        Can be used like this:
            denc = DictEncoder()
            @cherrypy.tools.json_out(handler=denc.json_handler)
        """
        value = cherrypy.serving.request._json_inner_handler(*args, **kwargs)
        return self.iterencode(value)


class BibleMungingServer(object):

    dictencoder = DictEncoder()

    def __init__(self, dbconn, bible, favorites, apptitle, appsubtitle, wordfilter):

        global scriptdir

        self._bible = bible
        self.connection = dbconn
        self.lock = threading.Lock()
        self.apptitle = apptitle
        self.appsubtitle = appsubtitle
        self.favorite_searches = favorites if favorites else []

        if wordfilter:
            from wordfilter import Wordfilter
            self.wordfilter = Wordfilter()
            self.wordfilter.add_words(['QwertyStringUsedForTestingZxcvb'])
        else:
            class wf:
                def blacklisted(self, string):
                    return False
            self.wordfilter = wf()

        deploymentinfofile = os.path.join(scriptdir, 'deploymentinfo.txt')
        try:
            with open(deploymentinfofile) as df:
                self.deploymentinfo = df.read()
        except:
            self.deploymentinfo = "development version"

        with self.lock:
            c = self.connection.cursor()
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='recent_searches'")
            if not c.fetchone():
                self.initialize_database()
            c.close()

    @classmethod
    def fromconfig(cls, configuration):
        # NOTE: this relies on a full pathname as 'dbpath' in the configuration
        dburi = "file://{}?cache=shared".format(os.path.abspath(configuration.get('biblemunger', 'dbpath')))
        dbconn = sqlite3.connect(dburi, uri=True, check_same_thread=False)

        bib = bible.Bible(dbconn)
        if not bib.initialized:
            bib.addversesfromxml(os.path.abspath(configuration.get('biblemunger', 'bible')))

        return BibleMungingServer(
            dbconn, bib,
            # Faves from the config file are a dictionary, but we need a list of {'search': search term, 'replace': replacement} objects
            [{'search': k, 'replace': v} for k, v in configuration['favorites'].items()],
            configuration.get('biblemunger', 'apptitle'),
            configuration.get('biblemunger', 'appsubtitle'),
            configuration.getboolean('biblemunger', 'wordfilter'))

    @property
    def recent_searches(self):
        with self.lock:
            c = self.connection.cursor()
            c.execute("SELECT search, replace FROM recent_searches")
            results = c.fetchall()
            c.close()
        return ({'search': result[0], 'replace': result[1]} for result in results)

    def initialize_database(self):
        with self.lock:
            c = self.connection.cursor()
            c.execute("CREATE TABLE recent_searches (search, replace)")
            self.connection.commit()
            c.close()

    def add_recent_search(self, search, replace):
        pair = {'search': search, 'replace': replace}
        if pair in self.favorite_searches or pair in self.recent_searches or self.wordfilter.blacklisted(replace):
            return
        with self.lock:
            c = self.connection.cursor()
            c.execute("INSERT INTO recent_searches VALUES (?, ?)", (search, replace))
            self.connection.commit()
            c.close()

    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPRedirect("munge")

    @cherrypy.expose
    @cherrypy.tools.json_out(handler=dictencoder.json_handler)
    def bible(self, search=None):
        if search:
            return self._bible.search(search)
        else:
            raise cherrypy.HTTPError(400, "No search terms")

    @cherrypy.expose
    @cherrypy.tools.mako(filename='munge.mako')
    def munge(self, search=None, replace=None):
        pagetitle = self.apptitle
        queried = False
        resultstitle = None
        results = None

        if search and replace:
            resultstitle = "{} ⇒ {}".format(search, replace)
            pagetitle = "{}: {}".format(self.apptitle, resultstitle)
            queried = True
            results = self._bible.replace(search, replace)
            if results:
                self.add_recent_search(search, replace)

        return {
            'pagetitle':      pagetitle,
            'apptitle':       self.apptitle,
            'appsubtitle':    self.appsubtitle,
            'queried':        queried,
            'resultstitle':   resultstitle,
            'results':        results,
            'favorites':      self.favorite_searches,
            'recents':        self.recent_searches,
            'search':         search,
            'replace':        replace,
            'deploymentinfo': self.deploymentinfo,
            'filterinuse':    bool(self.wordfilter)}


def configure():
    """Get biblemunger configuration

    NOTE: It's not currently possible to define more than 1 favorite replacement set with the same search term
    That is, if you put "search = replace1" and "search = replace2" in the config file, only the second will come through

    TODO: allow definition of multiple replacement sets with the same search term
    """

    global scriptdir

    # The first of these, the default config file, must exist (and is in git)
    # The second is an optional config file that can be provided by the user
    # NOTE: We want the config files to work even for WSGI, so we can't use a
    #       command line parameter for the user's config
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
    cpconfig = {
        '/': {
            'tools.mako.directories': os.path.join(scriptdir, 'temple'),
            'tools.staticdir.root': scriptdir},
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'static'},
        "/favicon.ico": {
            "tools.staticfile.on": True,
            "tools.staticfile.filename": os.path.join(scriptdir, 'static', 'favicon.ico')}}

    if mode == 'wsgi':
        sys.stdout = sys.stderr
        cherrypy.config.update({'environment': 'embedded'})
    elif mode == 'cherrypy':
        cherrypy.config.update({
            'server.socket_port': int(configuration.get('biblemunger', 'port')),
            'server.socket_host': configuration.get('biblemunger', 'server')})

    cherrypy.tree.mount(
        BibleMungingServer.fromconfig(configuration), '', cpconfig)

    if mode == 'wsgi':
        return cherrypy.tree(environ, start_response)
    elif mode == 'cherrypy':
        cherrypy.engine.start()
        cherrypy.engine.block()
