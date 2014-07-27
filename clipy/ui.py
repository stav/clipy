from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys
import curses
import threading

import pafy
import pyperclip

TITLE = '.:. Clipy .:.'
VIDEO = None

class Window(object):
    """Window absraction with border"""
    testing = False
    resource = None
    stream = None
    video = None

    def __init__(self, stdscr, lines, cols, y, x):
        self.stdscr = stdscr
        self.box = curses.newwin(lines, cols, y, x)
        Y, X = self.box.getmaxyx()
        # import pdb; pdb.set_trace()
        self.win = self.box.subwin(Y-2, X-4, y+1, 2)
        self.win.scrollok(True)
        self.win.keypad(True)

        self.box.box()

        # self._coord(Y-4, X-5)
        # for i in range(Y-2):
        #     self._coord(i, i)

    def _coord(self, y, x):
        self.win.addstr(y, x, '+ {} {}'.format(y, x))

    def display(self):
        self.win.erase()

        if self.video:
            self.printstr(self.video)

            self.printstr('Streams:')

            for i, stream in enumerate(self.video.allstreams):
                self.printstr('{}: {} {} {} {} {}'.format(i,
                    stream.mediatype,
                    stream.quality,
                    stream.extension,
                    stream.notes,
                    stream.bitrate or ''))

    def freshen(self):
        self.stdscr.noutrefresh()
        self.box.noutrefresh()
        self.win.noutrefresh()
        if not self.testing:
            curses.doupdate()

    def wait_for_input(self):
        return self.win.getch()

    def printstr(self, object, error=False):
        string = '{}\n'.format(object)
        if error:
            self.win.addstr(string, curses.A_BOLD | curses.color_pair(1))
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

    except (OSError, ValueError) as e:
        console.printstr(e, error=True)


def select(panel, console):
    if panel.video:
        panel.printstr('Press one of the numbers above to download (0-{})'
            .format(len(panel.video.allstreams)))

    else:
        console.printstr('No video to select streams, Inquire first', error=True)


def download(panel, console):
    download_dir = os.path.expanduser('~')
    try:
        stream = panel.stream
        path = '%s.%s' % (os.path.join(download_dir, stream.title), stream.extension)
        console.printstr('Downloading {} to {}'.format(stream, download_dir))
        f = stream.download(filepath=path, quiet=True, callback=panel.progress)

    except (OSError, ValueError, FileNotFoundError) as e:
        console.printstr(e, error=True)

    else:
        if f:
            console.printstr('Downloaded: "{}"'.format(f))


def cancel(panel, console):
    if panel.stream:
        console.printstr('Cancelling {}'.format(panel.stream))
        if panel.stream.cancel():
            console.printstr('Cancelled "{}"'.format(panel.stream.title))
    else:
        console.printstr('Nothing to cancel')

    panel.stream = None


def spawn(panel, console, index=None):
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
        else:
            panel.stream = panel.video.allstreams[index]

    t = threading.Thread(target=download, args=(panel, console))
    t.daemon = True
    t.start()


def loop(stdscr, panel, console):
    KEYS_CANCEL   = (ord('c'), ord('C'))
    KEYS_DOWNLOAD = (ord('d'), ord('D'))
    KEYS_INQUIRE  = (ord('i'), ord('I'))
    KEYS_NUMERIC  = range(48, 58)
    KEYS_PASTE    = (ord('p'), ord('P'))
    KEYS_QUIT     = (ord('q'), ord('Q'), 27)  # 27 is escape
    KEYS_SELECT   = (ord('s'), ord('S'))

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
            select(panel, console)

        if c in KEYS_DOWNLOAD:
            spawn(panel, console)

        if c in KEYS_NUMERIC:
            spawn(panel, console, c-48)

        if c in KEYS_CANCEL:
            cancel(panel, console)

        # Debug
        # stdscr.addstr(curses.LINES-1, 108, 'c={}, t={}      '.format(c, threading.active_count()))


def init(stdscr):
    if curses.has_colors():
        curses.start_color()

    # Setup curses
    menu_options = 'Press "P": paste, "I": inquire, "S": select, "D": download, "C": cancel, "Q": quit'
    curses.curs_set(False)
    curses.init_pair(1, curses.COLOR_RED  , curses.COLOR_BLACK)

    # Title bar at top
    stdscr.addstr(TITLE, curses.A_REVERSE)
    stdscr.chgat(-1, curses.A_REVERSE)

    # Menu options at bottom
    stdscr.addstr(curses.LINES-1, 0, menu_options)

    # Create container box
    # console = Window(stdscr, curses.LINES-2, curses.COLS, 1, 0)
    panel = Window(stdscr, curses.LINES-9, curses.COLS, 1, 0)
    console = Window(stdscr, 7, curses.COLS, curses.LINES-8, 0)

    # Load specified video if available
    if VIDEO:
        panel.video = VIDEO
        console.printstr('Loading video')
        inquire(panel, console)

    # Enter event loop
    loop(stdscr, panel, console)


def main(video=None):
    global VIDEO
    VIDEO = video
    curses.wrapper(init)

if __name__ == '__main__':
    main()
