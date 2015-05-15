# biblemunger - fuck with the holy scriptures

Inspired by [Mallory Ortberg's definitive text-replacement work](http://the-toast.net/tag/bible-verses/)

## CLI

Find the text "hearts": 

    biblemunger.py -s hearts

Replace "hearts" with "feels":

    biblemunger.py -s hearts -r feels

## Web

    biblemunger.py -w

## TODO

There's lots of room for improvement

- CSS not tables (lol)
- Mark up the replaced text. Allow client-side JS to embolden the replaced text with a checkbox.
- Allow replacement of multiple things at once.
  (Would love to be able to replace "sons" and "daughters" at the same time, for example.)
- Keep track of recent and popular replacements so that people can have things to click on when they first load the page
