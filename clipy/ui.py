# coding=utf-8
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys
import curses
import threading

from collections import OrderedDict

import pafy
import pyperclip

from .request import download as clipy_request_download

TITLE = '.:. Clipy .:.'
TARGET = None
VIDEO = None

class Window(object):
    """Window absraction with border"""
    testing = False
    resource = None
    stream = None
    streams=False
    video = None
    target = '~'
    lookups = OrderedDict()

    def __init__(self, stdscr, lines, cols, y, x):
        self.stdscr = stdscr

        # Border
        self.box = curses.newwin(lines, cols, y, x)
        Y, X = self.box.getmaxyx()
        self.box.box()

        # Inner window, left side
        self.win = self.box.subwin(Y-2, X//2, y+1, 2)
        self.win.scrollok(True)
        self.win.keypad(True)

        # Inner window, right side
        self.cache_x = X//2 + 4
        self.cache_index = None

        # self._coord(Y-4, X-5)
        # for i in range(Y-2):
        #     self._coord(i, i)

    def _coord(self, y, x):
        self.win.addstr(y, x, '+ {} {}'.format(y, x))

    def display(self):
        self.win.erase()

        if self.video:
            self.printstr(self.video)

            if self.streams:
                self.printstr('')
                self.printstr('Streams:')
                for i, stream in enumerate(self.video.allstreams):
                    self.printstr('{}: {} {} {} {} {}'.format(i,
                        stream.mediatype,
                        stream.quality,
                        stream.extension,
                        stream.notes,
                        stream.bitrate or ''))

        for i, lookup in enumerate(self.lookups):
            video = self.lookups[lookup]
            attr = curses.A_STANDOUT if i == self.cache_index else 0
            self.box.addstr(1+i, self.cache_x, '{i} - {dur}  {title}'.format(
                i=i, dur=video.duration, title=video.title), attr)

    def freshen(self):
        self.stdscr.noutrefresh()
        self.box.noutrefresh()
        self.win.noutrefresh()
        if not self.testing:
            curses.doupdate()

    def wait_for_input(self):
        return self.win.getch()

    def printstr(self, object='', success=False, error=False, wow=False):
        string = '{}\n'.format(object)
        if error:
            self.win.addstr(string, curses.A_BOLD | curses.color_pair(1))
        elif success:
            self.win.addstr(string, curses.color_pair(2))
        elif wow:
            self.win.addstr(string, curses.A_STANDOUT)
        else:
            self.win.addstr(string)
        self.freshen()

    def progress(self, total, *progress_stats):
        status_string = ('{:,} Bytes [{:.2%}] received. Rate: [{:4.0f} '
                         'KB/s].  ETA: [{:.0f} secs]')
        status = status_string.format(*progress_stats)
        self.stdscr.addstr(0, 15, status, curses.A_REVERSE)
        self.freshen()


def inquire(panel, console):
    console.printstr('Inquiring')
    try:
        if panel.resource:
            console.printstr('Resourse found: {}'.format(panel.resource))
            panel.video = pafy.new(panel.resource)
            panel.resource = None
            if panel.video.videoid not in panel.lookups:
                panel.lookups[panel.video.videoid] = panel.video

    except (OSError, ValueError) as e:
        console.printstr(e, error=True)


def cache(panel, console, key):
    # console.printstr(
    #   'key={} UP({}) DOWN({}), ci={} None({}), len={}'.format(
    #     key,
    #     key is curses.KEY_UP,
    #     key is curses.KEY_DOWN,
    #     panel.cache_index,
    #     panel.cache_index is None,
    #     len(panel.lookups),
    # ), wow=True)

    if panel.cache_index is None:
        panel.cache_index = 0

    else:

        if key == curses.KEY_UP:
            if panel.cache_index > 0:
                panel.cache_index -= 1

        elif key == curses.KEY_DOWN:
            if panel.cache_index < len(panel.lookups) -1:
                panel.cache_index += 1

        elif key == curses.KEY_ENTER or key == 10:
            if panel.cache_index >= 0 and panel.cache_index < len(panel.lookups):
                # console.printstr('lookups={}, index={}'.format(panel.lookups, panel.cache_index))
                panel.resource = list(panel.lookups)[panel.cache_index]
                # videoid = list(panel.lookups)[panel.cache_index]
                # panel.resource = panel.lookups[videoid]
                inquire(panel, console)

    # console.printstr('key={}, enter={}'.format(key, curses.KEY_ENTER))

    # console.printstr('key={}, ci={}, lups={}, cache_index is None={}'.format(
    #     key,
    #     panel.cache_index,
    #     len(panel.lookups),
    #     panel.cache_index is None,
    # ))

    # panel.display()


def select(panel, console):
    if panel.video:
        if panel.streams:
            console.printstr('Press one of the numbers above to download (0-{})'
                .format(len(panel.video.allstreams)-1))

    else:
        console.printstr('No video to select streams, Inquire first', error=True)


def cancel(panel, console):
    if panel.stream:
        console.printstr('Cancelling {}'.format(panel.stream))
        if panel.stream.cancel():
            console.printstr('Cancelled "{}"'.format(panel.stream.title))
    else:
        console.printstr('Nothing to cancel')

    panel.stream = None


def download(panel, console, index=None):
    if panel.video is None:
        console.printstr('No video to download, Inquire first', error=True)
        return
    if index is None:
        try:
            panel.stream = panel.video.getbest(preftype="mp4")
        except (OSError, ValueError) as e:
            console.printstr(e, error=True)
            return
    else:
        if index >= len(panel.video.allstreams):
            console.printstr('Stream {} not available'.format(index), error=True)
            return
        panel.stream = panel.video.allstreams[index]

    t = threading.Thread(target=clipy_request_download,
        args=(panel.stream, panel.target, console.printstr, panel.progress))
    t.daemon = True
    t.start()


def loop(stdscr, panel, console):
    KEYS_CANCEL   = (ord('x'), ord('X'))
    KEYS_DOWNLOAD = (ord('d'), ord('D'))
    KEYS_INQUIRE  = (ord('i'), ord('I'))
    KEYS_HELP     = (ord('h'), ord('H'))
    KEYS_PASTE    = (ord('p'), ord('P'))
    KEYS_SELECT   = (ord('s'), ord('S'))
    KEYS_QUIT     = (ord('q'), ord('Q'), 27)  # 27 is escape
    KEYS_CACHE    = (curses.KEY_UP, curses.KEY_DOWN, curses.KEY_ENTER, 10)
    KEYS_NUMERIC  = range(48, 58)

    while True:

        # Display video if available
        panel.display()

        # Refresh screen
        stdscr.noutrefresh()
        panel.freshen()
        console.freshen()
        curses.doupdate()

        # Blocking
        c = panel.wait_for_input()

        if c in KEYS_QUIT:
            break

        if c in KEYS_PASTE:
            panel.resource = pyperclip.paste().strip()
            console.printstr('Checking clipboard: {}'.format(panel.resource))
            inquire(panel, console)

        if c in KEYS_INQUIRE:
            inquire(panel, console)

        if c in KEYS_SELECT:
            panel.streams = not panel.streams
            select(panel, console)

        if c in KEYS_CACHE:
            cache(panel, console, c)

        if c in KEYS_DOWNLOAD:
            download(panel, console)

        if c in KEYS_NUMERIC:
            download(panel, console, c-48)

        if c in KEYS_CANCEL:
            cancel(panel, console)

        if c in KEYS_HELP:
            console.printstr('Help is on the way')

        # Debug
        stdscr.addstr(curses.LINES-1, curses.COLS-20, 'c={}, t={}      '.format(c, threading.active_count()))


def init(stdscr):
    if curses.has_colors():
        curses.start_color()

    # Setup curses
    curses.curs_set(False)
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)

    # Title bar at top
    stdscr.addstr(TITLE, curses.A_REVERSE)
    stdscr.chgat(-1, curses.A_REVERSE)

    # Menu options at bottom
    menu_options = (
        ('P', 'paste'),
        ('I', 'inquire'),
        ('S', 'select'),
        ('↑↓', 'cache'),
        ('⏎ ', 'cache'),
        ('D', 'download'),
        ('X', 'cancel'),
        ('H', 'help'),
        ('Q', 'quit'),
    )
    menu_string = 'Press: ' + ', '.join(
        ['{}: {}'.format(k, v) for k, v in menu_options])
    stdscr.addstr(curses.LINES-1, 0, menu_string)

    # Create container box
    panel = Window(stdscr, curses.LINES-9, curses.COLS, 1, 0)
    console = Window(stdscr, 7, curses.COLS, curses.LINES-8, 0)

    # Load command line options
    if TARGET:
        panel.target = TARGET
    if VIDEO:
        panel.video = VIDEO
        console.printstr('Loading video')
        inquire(panel, console)

    # Enter event loop
    loop(stdscr, panel, console)


def main(video=None, stream=None, target=None):
    global VIDEO, TARGET
    VIDEO = video
    TARGET = target
    curses.wrapper(init)

if __name__ == '__main__':
    main()
