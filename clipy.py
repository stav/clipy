import os, sys
import curses
import threading

import pafy
import pyperclip

TITLE = '.:. Clipy .:.'


class Window(object):
    """Window absraction with border"""

    def __init__(self, stdscr, lines, cols, y, x):
        self.stdscr = stdscr
        self.stream = None
        self.box = curses.newwin(lines, cols, y, x)
        Y, X = self.box.getmaxyx()
        self.win = self.box.subwin(Y-2, X-4, 2, 2)

        self.box.box()
        # self.coord(Y-4, X-5)
        # for i in range(Y-2):
        #     self.coord(i, i)

    def coord(self, y, x):
        self.win.addstr(y, x, '+ {} {}'.format(y, x))

    def freshen(self):
        self.stdscr.noutrefresh()
        self.box.noutrefresh()
        self.win.noutrefresh()
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


def download(window):
    download_dir = os.path.expanduser('~')
    try:
        best = window.video.getbest(preftype="mp4")
        window.stream = best
        path = '%s.%s' % (os.path.join(download_dir, best.title), best.extension)
        window.printstr('Downloading {} to {}'.format(best, download_dir))
        f = best.download(filepath=path, quiet=True, callback=window.progress)

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


def loop(stdscr, console):
    KEYS_QUIT = (ord('q'), ord('Q'), 27)  # 27 is escape
    KEYS_INQUIRE = (ord('i'), ord('I'))
    KEYS_DOWNLOAD = (ord('d'), ord('D'))
    KEYS_CANCEL = (ord('c'), ord('C'))

    while True:
        c = console.getch()

        if c in KEYS_QUIT:
            break

        if c in KEYS_INQUIRE:
            inquire(console)

        if c in KEYS_DOWNLOAD:
            t = threading.Thread(target=download, args=(console,))
            t.daemon = True
            t.start()

        if c in KEYS_CANCEL:
            cancel(console)

        # console.printstr(threading.active_count())

        stdscr.noutrefresh()
        console.freshen()
        curses.doupdate()


def init(stdscr):
    if curses.has_colors():
        curses.start_color()

    # menu_options = 'Press "I": inquire, "S": select, "D": download, "C": cancel, "Q": quit'
    menu_options = 'Press "I": inquire, "D": download, "C": cancel, "Q": quit'

    # curses.curs_set(False)
    curses.init_pair(1, curses.COLOR_RED  , curses.COLOR_BLACK)

    stdscr.addstr(TITLE, curses.A_REVERSE)
    stdscr.chgat(-1, curses.A_REVERSE)
    stdscr.addstr(curses.LINES-1, 0, menu_options)
    stdscr.addstr(curses.LINES-1, curses.COLS-15, str(curses.getsyx()))

    console = Window(stdscr, curses.LINES-2, curses.COLS, 1, 0)

    stdscr.noutrefresh()
    console.freshen()
    curses.doupdate()

    loop(stdscr, console)


def main():
    curses.wrapper(init)

if __name__ == '__main__':
    main()
