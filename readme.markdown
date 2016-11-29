# biblemunger - provacative text-replacement in famous literature

Inspired by [Mallory Ortberg's definitive text-replacement work](http://the-toast.net/series/bible-verses/)

## Requirements

 -  For the CLI, only Python3 is required.
 -  For the web server, the mako and cherrypy modules must be installed.
     -  You can install them from `pip`, if `pip3 install Mako CherryPy`
     -  Note that CherryPy for Python 3 in Ubuntu 14.04 LTS is version
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

A random list that should probably be pruned:

- Consider refactoring search/replace lists to be simple dictionaries?
- Use better version stamping system and/or something with the `__version__` attribute
- Allow replacement of multiple things at once.
  (Would love to be able to replace "sons" and "daughters" at the same time, for example.)
- Handle case, punctuation, whitespace more intuitively
- Should use a Mako page filter, rather than filtering on each expression
- Should filter on input side, in bmweb.py, in addition to output side, in index.mako. 
- Reverse the sorting of the recent searches
- More consistent layout would be nice, CSS is hard
- Paginate recent searches, or find another way to deal with potentially hundreds
- Show most searched

### BibleMunger 2.0: A big update

- Create text API
    - Bible converted to rows of SQL in database w/ columns: textId (e.g. KJV), bookId (e.g. Genesis), chapterId (e.g. 1), verseId (e.g. 1), data (e.g. "In the beginning...")
    - Write an API endpoint for searching these using literal strings (not regex) and returning verses using JSON or something similar
- Do text replacement in JavaScript
    - Obviates the command line tool, but I think that's ok
- Have the UI also talk to the database
    - No longer use URLs to save replacements (this wouldn't work well for multiple replacements anyway)
    - Instead, save replacement sets under a single ID and do something like http://example.com/munge?id=ReplacementSetId or whatever
    - Probably keep track of each ID's visit count and last-visit date so I can prune later if I need to
    - Have the ID change when the user changes the replacements list, and have the URL in the URL bar change to match it
    - Alternatively: have a code for replacements and pass that in the URL (perhaps base64 encoded? or is there something more efficient?), but then have a button to generate a shorter version of the link. This lets users work on their replacement set and only stores an ID in the database when they actually want to share it
    - That keeps the old-style behavior where you could just copy the URL in the address bar and send it to someone and have it work, as well
- Update UI to allow for substituting multiple things at once

Things that can be done at any time

- Handle results page
    - I don't like pagination, but that is a naive solution to the current problem of very large pages if you try to text-replace on "the"
- Add a reading mode to the app
    - This mode just reads the bible, can go directly to books/chapters/verses, whatever
- Allow creating a filter for all operations
    - ...including reading mode. This lets you create a replacement list and then reading sections with that replacement list enabled
    - Importantly, this would mean that in reading mode you'd see verses that don't match the search criteria normally alongside verses with munged text. This lets you get faux context for things, or do replacements in larger subsets (for instance, if a replacement in some verse were made funnier if it were seen alongside the previous/next verse)
- Be able to get context from each verse result
    - Perhaps have a `Verse Text (Book Chapter:Verse)` type format. Make "Book" and "Chapter" clickable, and when clicked, get the larger context but with the same replacements
    - Also consider having `Next`/`Back` buttons on each book/chapter/verse where appropriate
    - Obviously this goes hand in hand with a browse mode

### BibleMunger 2.1: MadLibs

- Create a replacement set with empty replacement values to designate a madlibs set
    - Maybe the replacements can have special values like `__n__` for noun?
    - Or maybe the UI is smart and has a dropdown menu or something?
- Also create a mode where the computer can pick a passage and replace words at random
    - (I assume there is some grammatical tagging of the KJV out there that I can use for free?)
- MadLibs sets have two modes:
    - edit mode looks like the normal search/replacement mode (the computer-generated madlibs would still expose this mode too)
    - play mode has two screens; the first asks for words in each required catagory, and the second fills them in for you; I'm figuring these screens would have large text UIs?
