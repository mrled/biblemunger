# biblemunger - fuck with the holy scriptures

Inspired by [Mallory Ortberg's definitive text-replacement work](http://the-toast.net/tag/bible-verses/)

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

