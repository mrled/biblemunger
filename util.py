import json
import sqlite3
import threading

import cherrypy
from mako.lookup import TemplateLookup


class MakoHandler(cherrypy.dispatch.LateParamPageHandler):
    """Callable which sets response.body"""

    def __init__(self, template, next_handler):
        self.template = template
        self.next_handler = next_handler

    def __call__(self):
        env = globals().copy()
        env.update(self.next_handler())

        # Get the base URL from cherrypy, and make sure that's always passed to the template renderer
        # That way, the 'baseurl' variable is always available, and functions that return these rendered templates don't have to remember to do anything before they can use it
        print('baseurl: ', cherrypy.url('/'))
        env.update({'baseurl': cherrypy.url('/')})

        return self.template.render(**env)


class MakoLoader(object):
    """A CherryPy loader for Mako templates which caches the templates in memory when they are loaded first time"""

    def __init__(self):
        self.lookups = {}

    def __call__(self, filename, directories, module_directory=None, collection_size=-1):
        # Find the appropriate template lookup.
        key = (tuple(directories), module_directory)
        try:
            lookup = self.lookups[key]
        except KeyError:
            lookup = TemplateLookup(
                directories=directories,
                module_directory=module_directory,
                collection_size=collection_size,
                input_encoding='utf-8',
                output_encoding='utf-8')
            self.lookups[key] = lookup
        cherrypy.request.lookup = lookup

        # Replace the current handler.
        cherrypy.request.template = lookup.get_template(filename)
        cherrypy.request.handler = MakoHandler(cherrypy.request.template, cherrypy.request.handler)


class DictEncoder(json.JSONEncoder):
    """JSON encoder for any object that can be encoded just by getting to its underlying .__dict__ attribute"""

    def default(self, obj):
        return obj.__dict__

    def cherrypy_json_handler(self, *args, **kwargs):
        """A handler for use with CherryPy

        Can be used like this:
            denc = DictEncoder()
            @cherrypy.tools.json_out(handler=denc.cherrypy_json_handler)
        """
        value = cherrypy.serving.request._json_inner_handler(*args, **kwargs)
        for chunk in self.iterencode(value):
            yield chunk.encode("utf-8")


class LockableSqliteConnection(object):
    """A class, usable as an argument to a 'with' statement, that has a sqlite3.Connection object, a sqlite3.Cursor object, and a threading.Lock object

    When the 'with' statement is begun, the internal cursor object is allocated, and the internal lock is acquired. When the 'with' statements terminates, the internal cursor object is closed, the internal connection object is committed, and the internal lock object is released. Exiting the 'with' statement does *not* close the connection; the caller is responsible for this, but we do provide a convenience method to do it.

    Usable like so:

        lockableconn = LockablesqliteConnection("file:///some/database.sqlite?cache=shared")
        with lockableconn as connection:
            connection.cursor.execute("SOME SQL HERE")
            results = connection.cursor.fetchall()

    Inside of the 'with' statement, take care not to call other code that will use a 'with' statement on the same LockableSqliteConnection object. This sounds obvious, but it's easy to do when the 'with' statement might be in another function which is itself called inside a 'with' statement. For instance, this code will fail:

        lockableconn = LockablesqliteConnection("file:///some/database.sqlite?cache=shared")
        def func1():
            with lockableconn as connection:
                connection.cursor.execute("SOME SQL HERE")
                results = connection.cursor.fetchall()
        def func2():
            with lockableconn as connection:
                func1()

    This class is intended to take the place of more cumbersome syntax like:

        lock = threading.Lock()
        dbconn = sqlite3.connect("file:///some/database.sqlite?cache=shared", uri=True, check_same_thread=False)
        with lock:
            with dbconn as connection:
                cursor = connection.cursor()
                cursor.execute("SOME SQL HERE")
                results = cursor.fetchall()
                connection.commit()
                cursor.close()
    """

    def __init__(self, dburi):
        self.lock = threading.Lock()
        self.connection = sqlite3.connect(dburi, uri=True, check_same_thread=False)
        self.cursor = None

    def __enter__(self):
        self.lock.acquire()
        self.cursor = self.connection.cursor()
        return self

    def __exit__(self, type, value, traceback):
        self.lock.release()
        self.connection.commit()
        # I've seen self.cursor be None before, but I'm not sure why
        # Attempting to call a method on None will throw an exception, though, so we'll check for it first
        if self.cursor is not None:
            self.cursor.close()
            self.cursor = None

    def close(self):
        """Close the underlying sqlite connection.

        Waits for current operations to finish. Renders the object basically useless.
        """
        self.lock.acquire()
        self.connection.close()
        self.lock.release()
