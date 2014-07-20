import os
import curses
import functools

import pafy
import pyperclip

TITLE = '.:. Clipy .:.'


class Window(object):
    """Window absraction with border"""

    print_line = 10

    def __init__(self, name, lines, cols, y, x):
        self.name = name
        self.box = curses.newwin(lines, cols, y, x)
        Y, X = self.box.getmaxyx()
        self.win = self.box.subwin(Y-2, X-4, 2, 2)

        self.box.box()
        self.win.box()
        self.box.addstr(self.name)
        self.coord(Y-4, X-5)
        for i in range(Y-2):
            self.coord(i, i)

    def coord(self, y, x):
        self.win.addstr(y, x, '+ {} {}'.format(y, x))

    def freshen(self):
        # self.box.refresh()
        # self.win.refresh()
        self.box.noutrefresh()
        self.win.noutrefresh()
        curses.doupdate()

    def getch(self):
        return self.win.getch()

    def printstr(self, string, indent=0, error=False):
        self.win.addstr(self.print_line, 0+indent, str(string))
        if error:
            self.win.addstr(self.print_line, 0, str(string), curses.A_BOLD | curses.color_pair(1))
        self.print_line += 1


def download(video):
    download_dir = os.path.expanduser('~')
    try:
        best = video.getbest(preftype="mp4")
        path = '%s.%s' % (os.path.join(download_dir, best.title), best.extension)
        print('Downloading', best, path)
        best.download(filepath=path)
    except (OSError, ValueError, FileNotFoundError) as e:
        print(e)


def inquire(window):
    def p(string='', indent=0):
        window.printstr(string, indent)

    def e(string):
        window.printstr(string, error=True)

    url = pyperclip.paste().strip()

    p('Checking clipboard:')
    p(url, 1)
    # p()
    try:
        video = pafy.new(url)
        p(video)
        p('allstreams: {}'.format(video.allstreams))

    except ValueError as ve:
        e(ve)


def loop(stdscr, console):
    while True:
        c = console.getch()

        if c == ord('q') or c == ord('Q'):
            break

        if c == ord('i') or c == ord('I'):
            inquire(console)

        stdscr.addstr(curses.LINES-1, curses.COLS-15, str(curses.getsyx()))

        stdscr.noutrefresh()
        console.freshen()
        curses.doupdate()


def main(stdscr):
    if curses.has_colors():
        curses.start_color()

    # curses.curs_set(False)
    # import pdb; pdb.set_trace()

    curses.init_pair(1, curses.COLOR_RED  , curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_BLUE , curses.COLOR_BLACK)

    stdscr.addstr(TITLE, curses.A_REVERSE)
    stdscr.chgat(-1, curses.A_REVERSE)
    stdscr.addstr(curses.LINES-1, 0, 'Press "Q": quit, "I": inquire')
    stdscr.addstr(curses.LINES-1, curses.COLS-15, str(curses.getsyx()))

    console = Window('Console', curses.LINES-2, curses.COLS, 1, 0)

    stdscr.noutrefresh()
    console.freshen()
    curses.doupdate()

    loop(stdscr, console)


if __name__ == '__main__':
    curses.wrapper(main)
