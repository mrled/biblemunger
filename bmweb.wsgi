"""
WSGI entry point for BibleMunger web application
"""

import os
import sys

import cherrypy

# Necessary because of WSGI; must be done before importing biblemunger
scriptdir = os.path.dirname(os.path.realpath(__file__))
sys.path = [scriptdir] + sys.path
import biblemunger


# Useful for logging WSGI applications
sys.stdout = sys.stderr

cherrypy.config.update({'environment': 'embedded'})
configuration = biblemunger.configure()
application = cherrypy.Application(
    biblemunger.BibleMungingServer.fromconfig(configuration),
    script_name=None,
    config=biblemunger.cp_root_config)
