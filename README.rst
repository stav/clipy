clipy
=====

*Command Line Interface using Python for Youtube*

Asynchronous Python command-line YouTube video downloader.

This project was created so I could learn Python's `asyncio` library.

Requirements
------------

The following Python versions are supported:

* Python 3.4

The following third-party libraries are used:

* ``aiohttp`` (asynchronous HTTP communication)
* ``pyperclip`` (optional, uses Gtk to read the clipboard)

Usage
-----

Download::

    clipy http://www.youtube.com/watch?v=fm78gjYkYKc -d

User Interface::

    clipy --ui

User interface written with ``curses`` from the standard library:

1. start script with ``--ui`` option
2. copy youtube url into clipboard
3. follow menu: I to inquire, D to download

Notes
-----

Only tested on Ubuntu Trusty and Mac Lion.

Python for Windows does not contain the needed `curses` library so the user
interface will not work "out of the box", perhaps ``UniCurses`` can help.
