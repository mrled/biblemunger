"""
- To run as WSGI, run this file (bmweb) directly
- To run using CherryPy's built-in webserver, run "biblemunger.py -w"
"""

import configparser
import os
import random
import sqlite3
import sys
# from pdb import set_trace as strace

import cherrypy
#from mako.template import Template
from mako.exceptions import RichTraceback
from mako.lookup import TemplateLookup

import biblemunger


class MakoHandler(cherrypy.dispatch.LateParamPageHandler):

    """Callable which sets response.body."""

    def __init__(self, template, next_handler):
        self.template = template
        self.next_handler = next_handler

    def __call__(self):
        env = globals().copy()
        env.update(self.next_handler())

        try:
            #rendered = self.template.render(**env)
            self.template.render(**env)
        except:
            traceback = RichTraceback()
            for (filename, lineno, function, line) in traceback.traceback:
                print('File {} line #{} function {}'.format(
                    filename,
                    lineno, function))
                print('    {}'.format(line))
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


class BibleMungingServer(object):

    def __init__(
            self,
            bible: biblemunger.Bible,
            favdict, #: list[dict],
            apptitle: str,
            appsubtitle: str,
            dbpath: str):

        self.bible = bible
        self.apptitle = apptitle
        self.appsubtitle = appsubtitle
        self.dbpath = dbpath

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
            biblemunger.Bible(configuration.get('biblemunger', 'bible')),
            configuration['favorites'],
            configuration.get('biblemunger', 'apptitle'),
            configuration.get('biblemunger', 'appsubtitle'),
            configuration.get('bmweb', 'dbpath'))

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
        c.execute(
            "select search, replace from recent_searches")
        results = c.fetchall()
        conn.close()
        searches = []
        for r in results:
            searches += [{'search': r[0], 'replace':r[1]}]
        return searches

    def initialize_database(self):
        conn = sqlite3.connect(self.dbpath)
        c = conn.cursor()
        c.execute('''create table recent_searches (search, replace)''')
        conn.commit()
        conn.close()

    def add_recent_search(self, search, replace):
        in_faves = self.search_in_list(self.favorite_searches, search, replace)
        in_recent = self.search_in_list(self.recent_searches, search, replace)
        if (in_faves or in_recent):
            return

        conn = sqlite3.connect(self.dbpath)
        c = conn.cursor()
        c.execute("insert into recent_searches values (?, ?)", (search, replace))
        conn.commit()
        conn.close()

    @cherrypy.expose
    @cherrypy.tools.mako(filename='index.mako')
    def index(self, search=None, replace=None):
        pagetitle = self.apptitle
        queried = False
        resultstitle = None
        results = None
        sampleresult = None

        if search and replace:
            #resultstitle = "{} &rArr; {}".format(search, replace)
            resultstitle = "{} ⇒ {}".format(search, replace)
            pagetitle = "{}: {}".format(self.apptitle, resultstitle)
            queried = True
            results = self.bible.replace(search, replace)
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
            'deploymentinfo': self.deploymentinfo}


def run(configuration):
    """
    Run a BibleMungingServer from CherryPy's web engine
    Useful in development; in production, you probably want to use bmweb.wsgi
    """
    global cp_root_config
    cherrypy.config.update({
        'server.socket_port': int(configuration.get('bmweb', 'port')),
        'server.socket_host': configuration.get('bmweb', 'server')})
    cherrypy.tree.mount(
        BibleMungingServer.fromconfig(configuration), 
        '/', cp_root_config)
    cherrypy.engine.start()
    cherrypy.engine.block()


scriptdir = os.path.dirname(os.path.realpath(__file__))
cp_root_config = {
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
