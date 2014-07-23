clipy
=====

_Command Line Interface using Python for Youtube._

Python commmand-line YouTube video downloader.

Requirements
------------

The following third-party libraries are used:

* pyperclip (uses Gtk to read the clipboard)
* Pafy (YouTube api)

Usage
-----

`clipy http://youtube.com/w...`

Menu option uses `curses`:

1. start script with `-m` option
2. copy youtube url into clipboard
3. follow menu: I to inquire, D to download

Notes
-----

Developed with Python 3 but should also work with Python 2.

Only tested on Ubuntu.

Python for Windows does not contain the needed `curses` library, perhaps
UniCurses can help.

Hardcoded to home directory download.
