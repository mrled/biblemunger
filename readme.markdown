# biblemunger - provacative text-replacement in famous literature

Inspired by [Mallory Ortberg's definitive text-replacement work](http://the-toast.net/series/bible-verses/)

## Requirements

- For the CLI, only Python3 is required.
- For the web server, the mako and cherrypy modules must be installed. 
  - Note that CherryPy for Python 3 in Ubuntu 14.04 LTS is version
    `3.2.2-4ubuntu5`, which is buggy, and the server will shut down a
    few seconds after it's started with an error like
    `cherrypy.process.wspbus.ChannelFailures: OSError("Port 8187 not
    bound on '127.0.0.1'",)`, even if the port open. Not sure if this
    applies to vanilla CherryPy 3.2.2.

## CLI

Find the text "hearts": 

    biblemunger.py -s hearts

Replace "hearts" with "feels":

    biblemunger.py -s hearts -r feels

## Web

    biblemunger.py -w

### Running in a subdirectory

The way the URLs work, subdirectory support isn't quite right when run from CherryPy directly. That is, having the app at `http://example.com/` works fine, but at `http://example.com/subdir` doesn't. This is because I couldn't figure out how to get CherryPy to redirect `/subapp` to `/subapp/`. 

### Running behind Apache

Apache can be configured to proxy requests to CherryPy, like so: 

    <Location /biblemunger/>
        Order allow,deny
        allow from all
        ProxyPass http://localhost:8187/
        ProxyPassReverse http://localhost:8187/
    </Location>

Furthermore, this can solve the subdirectory problem:

    Redirect permanent /biblemunger /biblemunger/

## TODO

- Allow replacement of multiple things at once.
  (Would love to be able to replace "sons" and "daughters" at the same time, for example.)
- Select the shortest verse for the `og:description` so you're most likely to see the whole thing when shared to FB etc
- Should use a Mako page filter, rather than filtering on each expression
- Should filter on input side, in bmweb.py, in addition to output side, in index.mako. 
- Reverse the sorting of the recent searches
- Fix the bug where recent searches appear more than once
- More consistent layout would be nice, CSS is hard

