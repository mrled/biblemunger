import base64
import collections
import json
import logging
import os
import sqlite3
import threading
# import urllib.parse

from enum import Enum

import cherrypy
from mako.lookup import TemplateLookup


SCRIPTDIR = os.path.dirname(os.path.realpath(__file__))
LOGGER = logging.getLogger('biblemunger')
LOGGER.addHandler(logging.NullHandler())


class MakoHandler(cherrypy.dispatch.LateParamPageHandler):
    """Callable which sets response.body

    Note that we provide some additional variable substitutions to the template, which all templates that are rendered using this handler may use without explicitly passing. For instance, the 'baseurl' variable is the base URL of the application.
    """

    def __init__(self, template, next_handler, debug=False):
        self.template = template
        self.next_handler = next_handler
        self.debug = debug

    def __call__(self):

        def dataUriFromStaticFile(filename, datatype):
            """Given a file relative to the static/ directory, return a data: URI containing a representation in base64

            filename: A file, relative to the static/ directory
            datatype: A data type for the URL, such as "image/png"
            """
            filepath = os.path.join(SCRIPTDIR, 'static', filename)
            with open(filepath, 'rb') as f:
                encoded = base64.b64encode(f.read()).decode()
            return "data:{};base64,{}".format(datatype, encoded)

        env = globals().copy()
        env.update(self.next_handler())
        baseurl = cherrypy.url('/')
        env.update({

            # The base URL of the application, wherever it's mounted
            'baseurl': baseurl,

            # A simple way to get a data: URL for a given static file
            'dataUriFromStaticFile': dataUriFromStaticFile,

            # Allow us to add useful debugging behavior at runtime
            'debug': self.debug})

        LOGGER.debug("MakoHandler(): rendering template {} from base {}".format(
            self.template, baseurl))

        return self.template.render(**env)


class MakoLoader():
    """A CherryPy loader for Mako templates which caches the templates in memory when they are loaded first time"""

    def __init__(self):
        self.lookups = {}

    def __call__(self, filename, directories, module_directory=None, collection_size=-1, debug=False):
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
        cherrypy.request.handler = MakoHandler(cherrypy.request.template, cherrypy.request.handler, debug=debug)


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


class LockableSqliteConnection():
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

    class Lsc():

        def __init__(self, connection, rw=False):
            self.lock = threading.Lock()
            self.connection = connection
            self.cursor = None
            self.rw = rw

        def __enter__(self):
            if self.rw:
                self.lock.acquire()
            self.cursor = self.connection.cursor()
            return self

        def __exit__(self, type, value, traceback):
            if self.rw:
                self.connection.commit()
            # I've seen self.cursor be None before, but I'm not sure why
            # Attempting to call a method on None will throw an exception, though, so we'll check for it first
            if self.cursor is not None:
                self.cursor.close()
                self.cursor = None
            if self.rw:
                self.lock.release()

        def close(self):
            if self.rw:
                self.lock.acquire()
            if self.cursor:
                self.cursor.close()
            if self.connection:
                self.connection.close()
            if self.rw:
                self.lock.release()

    def __init__(self, dburi):
        """Create a LockableSqliteConnection object.

        Assumes the dburi does *not* have the 'mode' querty parameter specified
        """

        # def paramadd(uri, params):
        #     """Add parameters to a URI query string"""
        #     parseduri = list(urllib.parse.urlparse(uri))
        #     query = dict(urllib.parse.parse_qsl(parseduri[4]))
        #     query.update(params)
        #     parseduri[4] = urllib.parse.urlencode(query)
        #     return urllib.parse.urlunparse(parseduri)

        def tryconnect(dburi):
            try:
                return sqlite3.connect(dburi, uri=True, check_same_thread=False)
            except:
                print("Failed to connect to database with URI '{}'".format(dburi))
                raise

        # TODO: Ideally roconn would enforce readonly connections to the databse, but for now it does not do this!
        # The following code will return 'sqlite3.OperationalError: unable to open database file', but I'm not sure why...
        # rodburi = paramadd(dburi, {'mode': 'ro'})
        # roconn = tryconnect(rodburi)

        roconn = tryconnect(dburi)
        rwconn = tryconnect(dburi)
        self.ro = self.Lsc(roconn)
        self.rw = self.Lsc(rwconn, rw=True)

    def __call__(self, mode='r'):
        if mode == 'r':
            return self.ro
        elif mode == 'w':
            return self.rw
        else:
            raise Exception("Invalid mode '{}'".format(mode))

    def close(self):
        """Close the underlying sqlite connections.

        Waits for current operations to finish. Renders the object basically useless.
        """
        self.ro.close()
        self.ro = None
        self.rw.close()
        self.rw = None


def normalizewhitespace(sql, formattokens=None):
    """A very stupid function that normalizes whitespace

    This lets me put arbitrary whitespace in a multi line string (the kind w/ 3 quote marks)

    It's useful for languages like SQL which sometimes need newlines and shit for readability, but for which whitespace is not important for execution

    It also lets me indent the text in my multi line strings in those scenarios
    """
    if isinstance(formattokens, str) or not isinstance(formattokens, collections.Iterable):
        formattokens = (formattokens, )
    return ' '.join(sql.split()).format(*tuple(formattokens))


class InitializationOption(Enum):
    """Options that control database table initialization

    NoAction:       Assume the table is already initialized
    InitIfNone      If the table doesn't exist, run the table creation SQL; if it does, do nothing
    Reinitialize:   Drop the table and then initialize it
    """

    NoAction = 0
    InitIfNone = 1
    Reinitialize = 2

    @classmethod
    def fromstr(cls, label):
        return cls[label]
