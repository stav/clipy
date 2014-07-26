from __future__ import absolute_import, division, print_function, unicode_literals

import argparse
import curses
import os
import sys
import threading

import pafy
# import pyperclip

TITLE = '.:. Clipy .:.'
VERSION = 0.5

class Window(object):
    """Window absraction with border"""
    stream = None
    testing = False
    video = None

    def __init__(self, stdscr, lines, cols, y, x):
        self.stdscr = stdscr
        self.box = curses.newwin(lines, cols, y, x)
        Y, X = self.box.getmaxyx()
        self.win = self.box.subwin(Y-2, X-4, 2, 2)
        self.win.scrollok(True)
        self.win.keypad(True)

        self.box.box()
        # self._coord(Y-4, X-5)
        # for i in range(Y-2):
        #     self._coord(i, i)

    def _coord(self, y, x):
        self.win.addstr(y, x, '+ {} {}'.format(y, x))

    def freshen(self):
        self.stdscr.noutrefresh()
        self.box.noutrefresh()
        self.win.noutrefresh()
        if not self.testing:
            curses.doupdate()

    def getch(self):
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


def inquire(window):
    url = pyperclip.paste().strip()

    window.printstr('Checking clipboard: {}'.format(url))
    try:
        video = pafy.new(url)
        window.printstr(video)
        window.printstr('allstreams: {}'.format(video.allstreams))
        window.video = video

    except (OSError, ValueError) as e:
        window.printstr(e, error=True)


def select(window):
    if window.video:
        window.printstr('Streams:')
        for i, stream in enumerate(window.video.allstreams):
            window.printstr('{}: {} {} {} {}'.format(i, stream.mediatype, stream.quality, stream.extension, stream.notes))
        window.printstr('Press one of the numbers above to download (0-{})'.format(i))

    else:
        window.printstr('No video to select streams, Inquire first', error=True)


def download(window):
    download_dir = os.path.expanduser('~')
    try:
        stream = window.stream
        path = '%s.%s' % (os.path.join(download_dir, stream.title), stream.extension)
        window.printstr('Downloading {} to {}'.format(stream, download_dir))
        f = stream.download(filepath=path, quiet=True, callback=window.progress)

    except (OSError, ValueError, FileNotFoundError) as e:
        window.printstr(e, error=True)

    else:
        if f:
            window.printstr('Downloaded: "{}"'.format(f))


def cancel(window):
    if window.stream:
        window.printstr('Cancelling {}'.format(window.stream))
        if window.stream.cancel():
            window.printstr('Cancelled "{}"'.format(window.stream.title))
    else:
        window.printstr('Nothing to cancel')
    window.stream = None


def spawn(window, index=None):
    if window.video is None:
        window.printstr('No video to download, Inquire first', error=True)
        return
    if index is None:
        try:
            window.stream = window.video.getbest(preftype="mp4")
        except (OSError, ValueError) as e:
            window.printstr(e, error=True)
            return
    else:
        if index >= len(window.video.allstreams):
            window.printstr('Stream {} not available'.format(index), error=True)
            return
        else:
            window.stream = window.video.allstreams[index]

    t = threading.Thread(target=download, args=(window,))
    t.daemon = True
    t.start()


def loop(stdscr, console):
    KEYS_QUIT = (ord('q'), ord('Q'), 27)  # 27 is escape
    KEYS_INQUIRE = (ord('i'), ord('I'))
    KEYS_SELECT = (ord('s'), ord('S'))
    KEYS_DOWNLOAD = (ord('d'), ord('D'))
    KEYS_CANCEL = (ord('c'), ord('C'))
    KEYS_NUMERIC = range(48, 58)

    while True:
        c = console.getch()

        if c in KEYS_QUIT:
            break

        if c in KEYS_INQUIRE:
            inquire(console)

        if c in KEYS_SELECT:
            select(console)

        if c in KEYS_DOWNLOAD:
            spawn(console)

        if c in KEYS_NUMERIC:
            spawn(console, c-48)

        if c in KEYS_CANCEL:
            cancel(console)

        # Debug
        # stdscr.addstr(curses.LINES-1, 108, 'c={}, t={}      '.format(c, threading.active_count()))

        # Refresh screen
        stdscr.noutrefresh()
        console.freshen()
        curses.doupdate()


def init(stdscr):
    if curses.has_colors():
        curses.start_color()

    # Setup curses
    menu_options = 'Press "I": inquire, "S": select, "D": download, "C": cancel, "Q": quit'
    curses.curs_set(False)
    curses.init_pair(1, curses.COLOR_RED  , curses.COLOR_BLACK)

    # Title bar at top
    stdscr.addstr(TITLE, curses.A_REVERSE)
    stdscr.chgat(-1, curses.A_REVERSE)

    # Menu options at bottom
    stdscr.addstr(curses.LINES-1, 0, menu_options)

    # Create container box
    console = Window(stdscr, curses.LINES-2, curses.COLS, 1, 0)

    # Refresh screen
    stdscr.noutrefresh()
    console.freshen()
    curses.doupdate()

    # Enter event loop
    loop(stdscr, console)


def _get_commandline_options():
    """
    >>> options = ['--qualify']
    >>> r = Router()
    >>> r.setup(options)
    >>> r.options
    Namespace... qualify=True...
    """
    # declare command-line argument parser
    command_line = argparse.ArgumentParser(
        description='YouTube video downloader',
        epilog='Refer to the documentation for more detailed information.',
        )

    # define the command-line arguments
    command_line.add_argument('-V', '--version', action='version',
                        version='%(prog)s version {}'.format(VERSION),
                        help='print the version information and exit')

    command_line.add_argument('-s', '--stream', metavar='S', type=int,
                        help='Stream to download: 0, 1, 2, 3...')

    command_line.add_argument('-d', '--download', action='store_true',
                        help='Downloaded a stream')

    command_line.add_argument('-m', '--menu', action='store_true',
                        help='Start the graphical menu')

    # command_line.add_argument('-i', dest='inputfile', nargs='?', metavar='INFL',
    #                     type=argparse.FileType('rU'), default=sys.stdin,
    #                     help='input filename, def=stdin')

    # command_line.add_argument('-o', dest='outputfile', metavar='OUFL', nargs='?',
    #                     type=argparse.FileType('w'), default=sys.stdout, const='/dev/null',
    #                     help='output filename, def=stdout, const=/dev/null')

    command_line.add_argument('-l', dest='logger', metavar='LOGFILE',
                        nargs='?', default=lambda *a: None, const=print,
                        help='Logging enabled, option must follow RESOURCE')

    # command_line.add_argument('-m', dest='mogrifyers', type=str, metavar='MGRFs',
    #                     help='mogrifyer classes "M1, M2,... Mn"')

    # command_line.add_argument('-p', dest='parser', type=str, metavar='PRSR',
    #                     help='parser class')

    command_line.add_argument('resource', metavar='RESOURCE', type=str, nargs='?',
                        help='URL or video Id')

    return command_line.parse_args(sys.argv[1:])


def main():
    """ Command line entry point """
    options = _get_commandline_options()
    log = options.logger
    video = None
    stream = None

    log('Clipy started with {}'.format(options))

    if options.resource:
        log('Supplied resouree: {}'.format(options.resource))
        video = pafy.new(options.resource)

    if video:
        log('Video found on YouTube ')
        print(video)
        for i, stream in enumerate(video.allstreams):
            print('{}: {} {} {} {} {}'.format(i,
                stream.mediatype,
                stream.quality,
                stream.extension,
                stream.notes,
                stream.bitrate or ''))

    # if options.download:
    #     stream = _get_stream(options)
    #     if stream:
    #         download()

    # if options.menu:
    #     curses.wrapper(init)

    log('Clipy stopping')

if __name__ == '__main__':
    main()