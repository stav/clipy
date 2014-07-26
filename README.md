clipy
=====

_Command Line Interface using Python for Youtube_

Python commmand-line YouTube video downloader.

Requirements
------------

The following third-party libraries are used:

* Pafy (mandatory, YouTube API)
* pyperclip (optional, uses Gtk to read the clipboard)

Usage
-----

Command line:

    clipy http://www.youtube.com/watch?v=fm78gjYkYKc -d -s1

User interface uses `curses`:

1. start script with `--ui` option
2. copy youtube url into clipboard
3. follow menu: I to inquire, D to download

Notes
-----

Developed with Python 3 but should also work with Python 2.

Only tested on Ubuntu.

Python for Windows does not contain the needed `curses` library, perhaps
UniCurses can help.
