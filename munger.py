import configparser
import json
import os
import sqlite3
import sys
# from pdb import set_trace as strace

import cherrypy
#from mako.template import Template
from mako.exceptions import RichTraceback
from mako.lookup import TemplateLookup

# Necessary because of WSGI; must be done before importing any modules in this directory
scriptdir = os.path.dirname(os.path.realpath(__file__))
sys.path = [scriptdir] + sys.path
import bible


def configure():
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

    def resolveconfigpath(path):
        return path if os.path.isabs(path) else os.path.join(scriptdir, path)

    configuration['biblemunger']['dbpath'] = resolveconfigpath(configuration['biblemunger']['dbpath'])
    configuration['biblemunger']['bible'] = resolveconfigpath(configuration['biblemunger']['bible'])

    return configuration


class MakoHandler(cherrypy.dispatch.LateParamPageHandler):
    """Callable which sets response.body."""

    def __init__(self, template, next_handler):
        self.template = template
        self.next_handler = next_handler

    def __call__(self):
        env = globals().copy()
        env.update(self.next_handler())
        try:
            self.template.render(**env)
        except:
            traceback = RichTraceback()
            for (filename, lineno, function, line) in traceback.traceback:
                print('File {} line #{} function {}\n    {}'.format(
                    filename, lineno, function, line))
            raise
        return self.template.render(**env)


class MakoLoader(object):

    def __init__(self):
        self.lookups = {}

    def __call__(
            self, filename, directories, module_directory=None,
            collection_size=-1):
        # Find the appropriate template lookup.
        key = (tuple(directories), module_directory)
        try:
            lookup = self.lookups[key]
        except KeyError:
            lookup = TemplateLookup(
                directories=directories,
                module_directory=module_directory,
                collection_size=collection_size)
            self.lookups[key] = lookup
        cherrypy.request.lookup = lookup

        # Replace the current handler.
        cherrypy.request.template = t = lookup.get_template(filename)
        cherrypy.request.handler = MakoHandler(t, cherrypy.request.handler)


cherrypy.tools.mako = cherrypy.Tool('on_start_resource', MakoLoader())


class DictEncoder(json.JSONEncoder):
    """JSON encoder for any object that can be encoded just by getting to its underlying .__dict__ attribute"""

    def default(self, obj):
        return obj.__dict__

    def iterencode(self, value):
        # Adapted from cherrypy/_cpcompat.py
        for chunk in super().iterencode(value):
            yield chunk.encode("utf-8")

    def json_handler(self, *args, **kwargs):
        # Adapted from cherrypy/lib/jsontools.py
        value = cherrypy.serving.request._json_inner_handler(*args, **kwargs)
        return self.iterencode(value)


class BibleMungingServer(object):

    dictencoder = DictEncoder()

    def __init__(self, bible, favdict, apptitle, appsubtitle, dbpath, wordfilter):

        self._bible = bible
        self.apptitle = apptitle
        self.appsubtitle = appsubtitle
        self.dbpath = dbpath

        if wordfilter:
            from wordfilter import Wordfilter
            self.wordfilter = Wordfilter()
            self.wordfilter.add_words(['QwertyStringUsedForTestingZxcvb'])
        else:
            self.wordfilter = False

        deploymentinfofile = os.path.join(scriptdir, 'deploymentinfo.txt')
        if os.path.exists(deploymentinfofile):
            with open(deploymentinfofile) as df:
                self.deploymentinfo = df.read()
        else:
            self.deploymentinfo = "development version"

        # TODO: refactor this, just use a dictionary directly elsewhere
        self.favorite_searches = []
        for key in favdict.keys():
            self.favorite_searches += [{'search': key, 'replace': favdict[key]}]

        conn = sqlite3.connect(self.dbpath)
        c = conn.cursor()
        c.execute(
            "select name from sqlite_master where type='table' and name='recent_searches'")
        if not c.fetchone():
            self.initialize_database()

    @classmethod
    def fromconfig(cls, configuration: configparser.ConfigParser):
        return BibleMungingServer(
            bible.Bible.fromxml(configuration.get('biblemunger', 'bible')),
            configuration['favorites'],
            configuration.get('biblemunger', 'apptitle'),
            configuration.get('biblemunger', 'appsubtitle'),
            configuration.get('biblemunger', 'dbpath'),
            configuration.getboolean('biblemunger', 'wordfilter'))

    def search_in_list(self, searchlist, search, replace):
        for s in searchlist:
            if s['search'] == search and s['replace'] == replace:
                return True
        else:
            return False

    @property
    def recent_searches(self):
        conn = sqlite3.connect(self.dbpath)
        c = conn.cursor()
        c.execute("select search, replace from recent_searches")
        results = c.fetchall()
        conn.close()
        return ({'search': result[0], 'replace': result[1]} for result in results)

    def initialize_database(self):
        conn = sqlite3.connect(self.dbpath)
        c = conn.cursor()
        c.execute('''create table recent_searches (search, replace)''')
        conn.commit()
        conn.close()

    def add_recent_search(self, search, replace):
        fave = self.search_in_list(self.favorite_searches, search, replace)
        recent = self.search_in_list(self.recent_searches, search, replace)
        filtered = self.wordfilter and self.wordfilter.blacklisted(replace)
        if (fave or recent or filtered):
            return

        conn = sqlite3.connect(self.dbpath)
        c = conn.cursor()
        c.execute("insert into recent_searches values (?, ?)", (search, replace))
        conn.commit()
        conn.close()

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
            #resultstitle = "{} &rArr; {}".format(search, replace)
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


def application(environ=None, start_response=None):
    """Webserver setup code

    If 'environ' and 'start_response' parameters are passed, assume WSGI.

    Otherwise, start cherrypy's built-in webserver.
    """

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
            "tools.staticfile.filename": os.path.join(
                scriptdir, 'static', 'favicon.ico')}
    }

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
