# biblemunger - provacative text-replacement in famous literature

Inspired by [Daniel Ortberg's definitive text-replacement work](http://the-toast.net/series/bible-verses/)

## ARCHIVED

**This project is now archived**

See the replacement project, which looks much nicer:

- <https://biblemunger.micahrl.com>
- <https://github.com/mrled/biblemungerjs>

## Requirements

- Python 3.4+
    - 3.4 is required for its version of sqlite (see below)
    - 3.4 is also required the `ensurepip` module
    - See below for conflicts with Mako, though
- sqlite 3.7.13
    - This version or later is required for shared cache mode, which is used heavily
- cherrypy: `pip install CherryPy`
    - Note: CherryPy for Python 3 in Ubuntu 14.04 LTS is version `3.2.2-4ubuntu5`, which is buggy, and the server will shut down a few seconds after it's started with an error like `cherrypy.process.wspbus.ChannelFailures: OSError("Port 8187 not bound on '127.0.0.1'",)`, even if the port free.
- mako: `pip install Mako`
    - It appears Mako 1.0.6 doesn't work with Python 3.6.0 or 3.6.1; when I try to install it using `pip`, I get an error like `AttributeError: module 'importlib._bootstrap' has no attribute 'SourceFileLoader'`. Various versions of Python 3.4 and 3.5 have worked for me in the past, and I'm using 3.5.3 as I type this.

You can install these dependencies separately, but it's often easiest to use `virtualenv`. Here's an example of how to do that with Python 3.4+ (which is required for the `ensurepip` module):

    python3 -m ensurepip                # Make sure you have pip
    python3 -m pip install virtualenv   # Make sure you have virtualenv
    python3 -m virtualenv venv          # Create a new virtualenv directory called 'venv'
    . venv/bin/activate                 # Activate your new virtual environment
    pip3 install CherryPy Mako          # Now that you've activated, install the dependencies
    python3 ./__main__.py               # Run BibleMunger in development mode

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

    python3 -m unittest discover

## Config file

The configuration file is in the loathesome JSON format, because I am lazy. There is no crying in baseball, and there are no comments in JSON. How chill would life be if we could just express our emotions, possibly when writing comments in our config files? I have literally no idea because we simply do not live in that world.

"Simply do not use json for your configs", you smirk. Yes, I thought of that. However, the configparser module does not support arrays (yes, really), and instead of writing a parser myself, I decided to write these beautiful paragraphs.

- `favorites`: A list of search terms and replacement tokens. Useful to define a few of these so that people have some examples on what to search for.
- `logfile`: If this is set, enable logging to a file
- `debug`: If true, show debugging information

## Roadmap

A random list that should probably be pruned:

- Use better version stamping system and/or something with the `__version__` attribute
- Handle case, punctuation, whitespace more intuitively
- More consistent layout would be nice, CSS is hard
- Show most searched
- Add a spinner for long loads. If you search a very common word rn like "God" it will take a couple of seconds
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
- Figure out why Python 3.6 won't work with Mako?

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
