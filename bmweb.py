import os
import random
import sqlite3
from pdb import set_trace as strace

import cherrypy
from mako.template import Template
from mako.exceptions import RichTraceback
from mako.lookup import TemplateLookup

import biblemunger

scriptdir = os.path.abspath(os.curdir)
templepath = os.path.join(scriptdir, 'temple')
dbname = 'bmweb.sqlite'

class MakoHandler(cherrypy.dispatch.LateParamPageHandler):
    """Callable which sets response.body."""
    def __init__(self, template, next_handler):
        self.template = template
        self.next_handler = next_handler
    def __call__(self):
        env = globals().copy()
        env.update(self.next_handler())

        try:
            rendered = self.template.render(**env)
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
    def __init__(self):
        self.bible = biblemunger.Bible('./kjv.xml')
        self.favorite_searches = [
            {'search':'hearts',        'replace':'feels'},
            {'search':'servant',       'replace':'uber driver'},
            {'search':'thy salvation', 'replace':'dat ass'},
            {'search':'staff',         'replace':'dick'}]

        conn = sqlite3.connect(dbname)
        c = conn.cursor()
        c.execute(
            "select name from sqlite_master where type='table' and name='recent_searches'")
        if not c.fetchone():
            self.initialize_database()

    def search_in_list(self, searchlist, search, replace):
        for s in searchlist:
            if s['search'] == search and s['replace'] == replace:
                return True
        else:
            return False

    @property
    def recent_searches(self):
        conn = sqlite3.connect(dbname)
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
        conn = sqlite3.connect(dbname)
        c = conn.cursor()
        c.execute('''create table recent_searches (search, replace)''')
        conn.commit()
        conn.close()

    def add_recent_search(self, search, replace):
        if (
                self.search_in_list(self.favorite_searches, search, replace) or
                self.search_in_list(self.recent_searches, search, replace)):
            return

        conn = sqlite3.connect(dbname)
        c = conn.cursor()
        c.execute("insert into recent_searches values (?, ?)", (search, replace))
        conn.commit()
        conn.close()

    @cherrypy.expose
    @cherrypy.tools.mako(filename='index.mako')
    def index(self, search=None, replace=None):
        pagetitle = biblemunger.apptitle
        queried = False
        resultstitle = None
        results = None
        
        if search and replace:
            resultstitle = "{} &rArr; {}".format(search, replace)
            pagetitle = "{}: {}".format(biblemunger.apptitle, resultstitle)
            queried = True
            results = self.bible.replace(search, replace)
            if results:
                self.add_recent_search(search, replace)

        return {
            'pagetitle':    pagetitle,
            'apptitle':     biblemunger.apptitle,
            'appsubtitle':  biblemunger.appsubtitle,
            'queried':      queried,
            'resultstitle': resultstitle,
            'results':      results,
            'favorites':    self.favorite_searches,
            'recents':      self.recent_searches,
            'search':       search,
            'replace':      replace}

def run():
    global scriptdir
    cherrypy.config.update({
        'server.socket_port': 8187, #BIBL
        'server.socket_host': '127.0.0.1'})
    fvicopath = "{}/static/favicon.ico".format(scriptdir)
    cp_root_config = {
        '/': {
            'tools.mako.directories': templepath,
            'tools.staticdir.root': scriptdir},
        '/static' : {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'static'},
        "/favicon.ico": {
            "tools.staticfile.on": True,
            "tools.staticfile.filename": fvicopath}
    }
        
    cherrypy.tree.mount(BibleMungingServer(), '/', cp_root_config)
    cherrypy.engine.start()
    cherrypy.engine.block()


