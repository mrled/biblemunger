# biblemunger - provacative text-replacement in famous literature

Inspired by [Mallory Ortberg's definitive text-replacement work](http://the-toast.net/series/bible-verses/)

## Requirements

- Python 3.4+
- sqlite 3.7.13 (required for shared cache mode)
- cherrypy: `pip install CherryPy`. Note: CherryPy for Python 3 in Ubuntu 14.04 LTS is version `3.2.2-4ubuntu5`, which is buggy, and the server will shut down a few seconds after it's started with an error like `cherrypy.process.wspbus.ChannelFailures: OSError("Port 8187 not bound on '127.0.0.1'",)`, even if the port open.
- mako: `pip install Mako`
- optional: the Wordfilter module: `pip install Wordfilter`

## Usage

For development use, this will start CherryPy's webserver:

    python3 ./__main__.py

If it's been installed via `pip`, this will start CherryPy's webserver:

    python3 -m biblemunger

If you want to run from Apache, consider using WSGI:

    <Directory /path/to/webapps>
        Options +ExecCGI 
        Require all granted
    </Directory>
    WSGIScriptAlias /biblemunger /path/to/webapps/biblemunger/munger.py

## Running the unit tests

The python `unittest` module is used:

    python -m unittest discover

## Config file

The configuration file is in the loathesome JSON format, because I am lazy. There is no crying in baseball, and there are no comments in JSON. How chill would life be if we could just express our emotions, possibly when writing comments in our config files? I have literally no idea because we simply do not live in that world.

"Simply do not use json for your configs", you smirk. Yes, I thought of that. However, the configparser module does not support arrays (yes, really), and instead of writing a parser myself, I decided to write these beautiful paragraphs.

- `wordfilter`: Set to `true` if you want to censor bad words from the replacement list.
- `favorites`: A list of search terms and replacement tokens. Useful to define a few of these so that people have some examples on what to search for.
- `logfile`: If this is set, enable logging to a file
- `debug`: If true, show debugging information

## Roadmap

A random list that should probably be pruned:

- Use better version stamping system and/or something with the `__version__` attribute
- Handle case, punctuation, whitespace more intuitively
- Reverse the sorting of the recent searches
- More consistent layout would be nice, CSS is hard
- Show most searched
- Add a spinner for long loads. If you search a very common word rn like "God" it will take a couple of seconds
- How to paginate the recent searches list? Or how to prune it?
- Tests
    - Calculate test coverage
    - Write tests until I hit 100% coverage
    - How to test CherryPy apps: http://docs.cherrypy.org/en/latest/advanced.html#testing-your-application
    - How to test CherryPy apps without running the full server: https://bitbucket.org/Lawouach/cherrypy-recipes/src/1a27059966e962be52b2abd91e9709c3ee63cf2d/testing/unit/serverless/test.py?at=default&fileviewer=file-view-default
    - Write integrations tests for the backend
    - Also, test the frontend
- Investigate the need for polyfills for older browsers
    - history.pushState / the popstate event
    - XMLHttpRequest
- Minify and compress
    - Python can minify CSS and JS, and even HTML, if you wanna use an external library
    - However, I was having trouble integrating this with Mako, so I gave up for now
    - Can CherryPy compress it automatically? (If so, will that work when run as WSGI?)
- LockableSqliteConnection():
    - Modify this to provide read-only and read-write access to the database, depending on what the caller needs
    - Consider not locking the database for reads?
    - I thnk I would have an external class, and an interanal class. The internal class would look mostly like the class does now; the external class would implement a `.open()` (? or maybe a better name) that would return the internal class.
    - Since the internal class implements `__enter__()` and `__exit__()`, it can be used with the `with` statement; since the `.open()` method will return the internal class, you can `with lsc.open() as whatever:` and it'll work
    - However, the important new feature is that you can accept other arguments to `.open()` - such as a flag representing read only or read/write access, like the `open()` builtin does

### BibleMunger 2.0: A big update

- Have the UI also talk to the database
    - No longer use URLs to save replacements (this wouldn't work well for multiple replacements anyway)
    - Instead, save replacement sets under a single ID and do something like http://example.com/munge?id=ReplacementSetId or whatever
    - Probably keep track of each ID's visit count and last-visit date so I can prune later if I need to
    - Have the ID change when the user changes the replacements list, and have the URL in the URL bar change to match it
    - Alternatively: have a code for replacements and pass that in the URL (perhaps base64 encoded? or is there something more efficient?), but then have a button to generate a shorter version of the link. This lets users work on their replacement set and only stores an ID in the database when they actually want to share it
    - That keeps the old-style behavior where you could just copy the URL in the address bar and send it to someone and have it work, as well
- Update UI to allow for substituting multiple things at once
- Handle results page
    - I don't like pagination, but that is a naive solution to the current problem of very large pages if you try to text-replace on "the"
    - Idea from Ben: use infinite scrolling, but also provide metrics like "X of Y results have been loaded" and a button to load all remaining verses
- Add a reading mode to the app
    - This mode just reads the bible, can go directly to books/chapters/verses, whatever
- Allow creating a filter for all operations
    - ...including reading mode. This lets you create a replacement list and then reading sections with that replacement list enabled
    - Importantly, this would mean that in reading mode you'd see verses that don't match the search criteria normally alongside verses with munged text. This lets you get faux context for things, or do replacements in larger subsets (for instance, if a replacement in some verse were made funnier if it were seen alongside the previous/next verse)
- Be able to get context from each verse result
    - Perhaps have a `Verse Text (Book Chapter:Verse)` type format. Make "Book" and "Chapter" clickable, and when clicked, get the larger context but with the same replacements
    - Also consider having `Next`/`Back` buttons on each book/chapter/verse where appropriate
    - Obviously this goes hand in hand with a browse mode
- Keep track of how many times each search/replace pair gets loaded.
    - Can we keep track of unique visits without saving tracking data like IP addresses or cookies?
- Get a mocked up single page app to Ben so he can play with it
    - Should return dummy data (like maybe the same 5 verses for all search/replace ops)
    - Should not require the backend to be running
    - Running locally might be tough but maybe as a GH page? Could even use the gh-pages branch of this repo... then all changes are visible instantly

### BibleMunger 2.1: MadLibs

- Create a replacement set with empty replacement values to designate a madlibs set
    - Maybe the replacements can have special values like `__n__` for noun?
    - Or maybe the UI is smart and has a dropdown menu or something?
- Also create a mode where the computer can pick a passage and replace words at random
    - (I assume there is some grammatical tagging of the KJV out there that I can use for free?)
- MadLibs sets have two modes:
    - edit mode looks like the normal search/replacement mode (the computer-generated madlibs would still expose this mode too)
    - play mode has two screens; the first asks for words in each required catagory, and the second fills them in for you; I'm figuring these screens would have large text UIs?

### Far future?

- Other translations? KJV seems especially funny but others might be more familiar to people
- Other texts altogether? Would be cool if there were a good way to have it be extensible, but most other texts don't have a book/chapter/verse so nicely set out for us so I'm not sure how it would work.
