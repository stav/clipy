import os, sys
import curses
import threading

import pafy
import pyperclip

TITLE = '.:. Clipy .:.'


class Window(object):
    """Window absraction with border"""

    def __init__(self, lines, cols, y, x):
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
        self.box.noutrefresh()
        self.win.noutrefresh()
        curses.doupdate()

    def getch(self):
        return self.win.getch()

    def printstr(self, object, indent=0, error=False):
        string = '{}\n'.format(object)
        if error:
            self.win.addstr(string, curses.A_BOLD | curses.color_pair(1))
        else:
            self.win.addstr(string)
        self.freshen()

    def progress(self, total, *progress_stats):
        status_string = ('STAV!!!  {:,} Bytes [{:.2%}] received. Rate: [{:4.0f} '
                         'KB/s].  ETA: [{:.0f} secs]')

        status = status_string.format(*progress_stats)
        sys.stdout.write("\r" + status + ' ' * 4 + "\r")
        # sys.stdout.flush()

def download(window):
    download_dir = os.path.expanduser('~')
    try:
        best = window.video.getbest(preftype="mp4")
        path = '%s.%s' % (os.path.join(download_dir, best.title), best.extension)
        print('Downloading', best, path)
        best.download(filepath=path, quiet=False, callback=window.progress)
    except (OSError, ValueError, FileNotFoundError) as e:
        print(e)
    window.printstr('')
    window.printstr('DONE!!!!')


def inquire(window):
    def p(string='', indent=0):
        window.printstr(string, indent)

    def e(string):
        window.printstr(string, error=True)

    url = pyperclip.paste().strip()

    p('Checking clipboard: {}'.format(url))
    try:
        video = pafy.new(url)
        p(video)
        p('allstreams: {}'.format(video.allstreams))
        window.video = video

    except ValueError as ve:
        e(ve)


def loop(stdscr, console):
    while True:
        c = console.getch()

        if c == ord('q') or c == ord('Q'):
            break

        if c == ord('i') or c == ord('I'):
            inquire(console)

        if c == ord('d') or c == ord('D'):
            t = threading.Thread(target=download, args=(console,))
            t.daemon = True
            t.start()

        stdscr.addstr(curses.LINES-1, curses.COLS-15, str(curses.getsyx()))

        stdscr.noutrefresh()
        console.freshen()
        curses.doupdate()


def main(stdscr):
    if curses.has_colors():
        curses.start_color()

    curses.curs_set(False)
    curses.init_pair(1, curses.COLOR_RED  , curses.COLOR_BLACK)

    stdscr.addstr(TITLE, curses.A_REVERSE)
    stdscr.chgat(-1, curses.A_REVERSE)
    stdscr.addstr(curses.LINES-1, 0, 'Press "I": inquire, "D": download, "Q": quit')
    stdscr.addstr(curses.LINES-1, curses.COLS-15, str(curses.getsyx()))

    console = Window(curses.LINES-2, curses.COLS, 1, 0)

    stdscr.noutrefresh()
    console.freshen()
    curses.doupdate()

    loop(stdscr, console)


if __name__ == '__main__':
    curses.wrapper(main)
