# coding=utf-8
"""
Clipy YouTube video downloader user interface
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import curses
import threading
import subprocess

from collections import OrderedDict

import pafy
import pyperclip

from .request import download as clipy_request_download

TITLE = '.:. Clipy .:.'
VERSION = '0.7'


class CacheList(OrderedDict):
    """docstring for CacheList"""
    def __init__(self, name):
        super(CacheList, self).__init__()
        self.name = name
        self.index = None


class Video(object):
    """Pafy video encapsulation"""
    def __init__(self, video):
        self.video = video

    def __str__(self):
        return '{dur}  {title}'.format(
            dur=self.video.duration, title=self.video.title)


class Stream(object):
    """Pafy stream encapsulation"""
    def __init__(self, stream, filename):
        self.stream = stream
        self.filename = filename

    def __str__(self):
        return str(self.filename)


class Window(object):
    """
    Window absraction with border
    """
    win = box = None
    testing = False

    def __init__(self, stdscr, lines, cols, y, x):
        self.stdscr = stdscr

        # Border
        self.box = curses.newwin(lines, cols, y, x)
        Y, X = self.box.getmaxyx()
        self.box.box()

       # Inner window
        Y, X = self.box.getmaxyx()
        self.win = self.box.subwin(Y-2, X-3, y+1, x+2)
        self.win.scrollok(True)
        self.win.keypad(True)

        # Debug
        # self._coord(Y-4, X-5)
        # for i in range(Y-2):
        #     self._coord(i, i)

    def _coord(self, y, x):
        self.win.addstr(y, x, '+ {} {}'.format(y, x))

    def display(self):
        self.win.erase()
        self.box.erase()
        self.box.box()

    def load(self):
        class Cache(): pass

        with open('clipy.lookups', 'r') as f:
            for line in f.readlines():
                key, duration, title = line.split(maxsplit=2)
                # self.printstr('{} {} {}.'.format(key, duration, title))
                video = Cache()
                video.videoid = key
                video.duration = duration
                video.title = title.strip()
                self.lookups[key] = Video(video)

        with open('clipy.downloads', 'r') as f:
            for line in f.readlines():
                url, filename = line.split(maxsplit=1)
                stream = Cache()
                stream.url = url
                self.downloads[url] = Stream(stream, filename.strip())

    def save(self):
        with open('clipy.lookups', 'w') as f:
            for key in self.lookups:
                cache = self.lookups[key]
                f.write('{} {}\n'.format(cache.video.videoid, cache))

        with open('clipy.downloads', 'w') as f:
            for key in self.downloads:
                cache = self.downloads[key]
                f.write('{} {}\n'.format(cache.stream.url, cache))

    def freshen(self):
        self.box.noutrefresh()
        self.win.noutrefresh()

    def printstr(self, text='', success=False, error=False, wow=False):
        string = '\n{}'.format(text)
        if error:
            self.win.addstr(string, curses.A_BOLD | curses.color_pair(1))
        elif success:
            self.win.addstr(string, curses.color_pair(2))
        elif wow:
            self.win.addstr(string, curses.A_STANDOUT)
        else:
            self.win.addstr(string)

    def progress(self, total, *progress_stats):
        status_string = ('{:,} Bytes [{:.2%}] received. Rate: [{:4.0f} '
                         'KB/s].  ETA: [{:.0f} secs]')
        status = status_string.format(*progress_stats)
        self.stdscr.addstr(0, 15, status, curses.A_REVERSE)
        self.stdscr.noutrefresh()
        curses.doupdate()


class DetailWindow(Window):
    """
    Window with video info
    """
    resource = None
    stream = None
    streams = False
    target = '~'
    video = None

    def display(self):
        super(DetailWindow, self).display()

        # Display video detail
        if self.video:
            self.printstr(self.video)

            # Display streams only if toggled
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

        self.freshen()


class ListWindow(Window):
    """
    Window with cache storage and list capabilities
    """
    caches = (
        CacheList('Lookups'),
        CacheList('Downloads'),
    )
    lookups = caches[0]
    downloads = caches[1]
    videos = lookups

    def display(self):
        super(ListWindow, self).display()

        # Display list of video caches
        for i, cache in enumerate(self.caches):
            # self.printstr('{}: {} {} {}'.format(i, cache.name, self.videos.name, cache.name == self.videos.name))
            attr = curses.A_STANDOUT if cache.name == self.videos.name else 0
            self.box.addstr(1, 20+20*i, cache.name.upper(), attr)

        # Display video list
        self.box.addstr(2, 2, self.videos.name)
        for i, key in enumerate(self.videos):
            video = self.videos[key]
            attr = curses.A_STANDOUT if i == self.videos.index else 0
            self.box.addstr(3+i, 2, str(video), attr)

        self.freshen()


class Panel(object):
    """docstring for Panel"""
    testing = False

    def __init__(self, detail_panel, list_panel, console):
        self.detail_panel = detail_panel
        self.list_panel = list_panel
        self.console = console

    def display(self):
        self.detail_panel.display()
        self.list_panel.display()
        self.console.freshen()

    def freshen(self):
        self.detail_panel.freshen()
        self.list_panel.freshen()
        self.console.freshen()
        # if not self.testing:
        #     curses.doupdate()

    # def load_video(self, video):
    #     self.console.printstr('Loading video: {}'.format(video.title))
    #     self.detail_panel.video = video

    #     if self.detail_panel.video.videoid not in self.list_panel.lookups:
    #         self.list_panel.lookups[self.detail_panel.video.videoid] = Video(self.detail_panel.video)

    def inquire(self, resource):
        try:
            self.console.printstr('Resourse: {}'.format(resource))
            self.detail_panel.video = pafy.new(resource)

        except (OSError, ValueError) as e:
            self.console.printstr(e, error=True)

        else:
            if self.detail_panel.video.videoid not in self.list_panel.lookups:
                self.list_panel.lookups[self.detail_panel.video.videoid] = Video(self.detail_panel.video)

    def wait_for_input(self):
        return self.detail_panel.win.getch()

    def cache(self, key):
        if key == ord('L'):
            self.list_panel.load()

        elif key == ord('C'):
            self.list_panel.save()

        elif key == curses.KEY_LEFT:
            self.list_panel.videos = self.list_panel.lookups

        elif key == curses.KEY_RIGHT:
            self.list_panel.videos = self.list_panel.downloads

        else:
            if self.list_panel.videos.index is None:
                self.list_panel.videos.index = 0

            if key == curses.KEY_UP:
                if self.list_panel.videos.index > 0:
                    self.list_panel.videos.index -= 1

            elif key == curses.KEY_DOWN:
                if self.list_panel.videos.index < len(self.list_panel.videos) -1:
                    self.list_panel.videos.index += 1

            elif key == curses.KEY_ENTER or key == 10:
                if self.list_panel.videos.index >= 0 and self.list_panel.videos.index < len(self.list_panel.videos):
                    if self.list_panel.videos == self.list_panel.lookups:
                        self.inquire(list(self.list_panel.videos)[self.list_panel.videos.index])
                    else:
                        key = list(self.list_panel.videos)[self.list_panel.videos.index]
                        filename = self.list_panel.videos[key].filename
                        try:
                            self.console.printstr(filename, wow=True)
                            subprocess.call(['mplayer', '{}'.format(filename)], shell=False)
                        except Exception as e:
                            import pdb; pdb.set_trace()
                            self.console.printstr(e, error=True)


    def select(self):
        self.detail_panel.streams = not self.detail_panel.streams
        if self.detail_panel.video:
            if self.detail_panel.streams:
                self.console.printstr('Press one of the numbers above to download (0-{})'
                    .format(len(self.detail_panel.video.allstreams)-1))

        else:
            console.printstr('No video to select streams, Inquire first', error=True)


    def cancel(self):
        if self.detail_panel.stream:
            self.console.printstr('Cancelling {} `{}`'.format(self.detail_panel.stream, self.detail_panel.stream.title))
            if self.detail_panel.stream.cancel():
                self.console.printstr('Cancelled {} `{}`'.format(self.detail_panel.stream, self.detail_panel.stream.title))
        else:
            self.console.printstr('Nothing to cancel')

        self.detail_panel.stream = None


    def download(self, index=None):

        def done(stream, filename, success):
            if success:
                self.list_panel.downloads[stream.url] = Stream(stream, filename)
            self.list_panel.display()
            self.console.freshen()
            if not self.testing:
                curses.doupdate()

        if self.detail_panel.video is None:
            self.console.printstr('No video to download, Inquire first', error=True)
            return

        if index is None:
            try:
                self.detail_panel.stream = self.detail_panel.video.getbest(preftype="mp4")
            except (OSError, ValueError) as e:
                self.console.printstr(e, error=True)
                return
        else:
            if index >= len(self.detail_panel.video.allstreams):
                self.console.printstr('Stream {} not available'.format(index), error=True)
                return
            self.detail_panel.stream = self.detail_panel.video.allstreams[index]

        t = threading.Thread(
            target=clipy_request_download,
            args=(
                self.detail_panel.stream,
                self.detail_panel.target,
                self.console.printstr,
                self.detail_panel.progress,
                done,
            ))
        t.daemon = True
        t.start()


def loop(stdscr, panel):
    KEYS_NUMERIC  = range(48, 58)
    KEYS_CANCEL   = (ord('x'), ord('X'))
    KEYS_DOWNLOAD = (ord('d'), ord('D'))
    KEYS_INQUIRE  = (ord('i'), ord('I'))
    KEYS_HELP     = (ord('h'), ord('H'))
    # KEYS_PASTE    = (ord('p'), ord('P'))
    KEYS_SELECT   = (ord('s'), ord('S'))
    KEYS_QUIT     = (ord('q'), ord('Q'), 27)  # 27 is escape
    KEYS_CACHE    = (ord('L'), ord('C'), curses.KEY_LEFT, curses.KEY_RIGHT,
        curses.KEY_UP, curses.KEY_DOWN, curses.KEY_ENTER, 10)  # 10 is enter

    while True:

        # Refresh screen
        stdscr.noutrefresh()
        panel.display()
        # panel.freshen()
        curses.doupdate()

        # Blocking
        c = panel.wait_for_input()

        if c in KEYS_QUIT:
            break

        # if c in KEYS_PASTE:
        if c in KEYS_INQUIRE:
            resource = pyperclip.paste().strip()
            panel.console.printstr('Checking clipboard: {}'.format(resource))
            panel.inquire(resource)

        if c in KEYS_SELECT:
            panel.select()

        if c in KEYS_CACHE:
            panel.cache(c)

        if c in KEYS_DOWNLOAD:
            panel.download()

        if c in KEYS_NUMERIC:
            panel.download(c-48)

        if c in KEYS_CANCEL:
            panel.cancel()

        if c in KEYS_HELP:
            panel.console.printstr('Help is on the way')

        # Debug
        stdscr.addstr(curses.LINES-1, curses.COLS-20, 'c={}, t={}      '
            .format(c, threading.active_count()))


def init(stdscr, video, stream, target):

    # Setup curses
    curses.curs_set(False)
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
    if curses.has_colors():
        curses.start_color()

    # Title bar at top
    stdscr.addstr(TITLE, curses.A_REVERSE)
    stdscr.chgat(-1, curses.A_REVERSE)

    # Menu options at bottom
    menu_options = (
        # ('P', 'paste'),
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

    # Create the middle three windows
    detail_panel  = DetailWindow(stdscr, curses.LINES-9, curses.COLS//2,              1, 0                           )
    list_panel    = ListWindow  (stdscr, curses.LINES-9, curses.COLS//2,              1, curses.COLS - curses.COLS//2)
    console       = Window      (stdscr, 7             , curses.COLS   , curses.LINES-8, 0                           )
    control_panel = Panel(detail_panel, list_panel, console)

    # Load command line options
    detail_panel.video = video
    detail_panel.stream = stream
    detail_panel.target = target

    # Enter event loop
    loop(stdscr, control_panel)


def main(video=None, stream=None, target=None):
    """
    Single entry point
    """
    curses.wrapper(init, video, stream, target)

if __name__ == '__main__':
    main()
