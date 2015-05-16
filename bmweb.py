import os

import cherrypy
from mako.template import Template
from mako.exceptions import RichTraceback
from mako.lookup import TemplateLookup

import biblemunger

scriptdir = os.path.abspath(os.curdir)
templepath = os.path.join(scriptdir, 'temple')

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
            if config.getboolean('debug'):
                traceback = RichTraceback()
                for (filename, lineno, function, line) in traceback.traceback:
                    print('File {} line #{} function {}'.format(filename, 
                        lineno, function))
                    print('    {}'.format(line))
            else:
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

    @cherrypy.expose
    @cherrypy.tools.mako(filename='index.mako')
    def index(self, search=None, replace=None):
        pagetitle = biblemunger.apptitle
        queried = False
        resultstitle = None
        results = None
        
        if search and replace:
            #resultstitle = "cat kjv | sed s/{}/{}/g".format(search, replace)
            resultstitle = "{} &rArr; {}".format(search, replace)
            pagetitle = "{} - {}".format(biblemunger.apptitle, resultstitle)
            results = self.bible.replace(search, replace)
            queried = True

        favorites = [
            {'search':'hearts',     'replace':'feels'},
            {'search':'servant',    'replace':'uber driver'},
            {'search':'exile',      'replace':'otaku'},
            {'search':'the saints', 'replace':'my waifu'}]

        return {
            'pagetitle':    pagetitle,
            'apptitle':     biblemunger.apptitle,
            'appsubtitle':  biblemunger.appsubtitle,
            'queried':      queried,
            'resultstitle': resultstitle,
            'results':      results,
            'favorites':    favorites,
            'search':       search,
            'replace':      replace}

def run():
    global scriptdir
    cherrypy.config.update({
        'server.socket_port': 8187,        #BIBL
        'server.socket_host': '0.0.0.0'})
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


