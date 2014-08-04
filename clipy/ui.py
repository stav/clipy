# coding=utf-8
"""
Clipy YouTube video downloader user interface
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import curses
import threading
import subprocess

from collections import OrderedDict

import pafy
import pyperclip

from .request import download as clipy_request_download

TITLE = '.:. Clipy .:.'
VERSION = '0.7.4'


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

    def __init__(self, lines, cols, y, x):
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
        # Display immediately
        self.freshen()
        curses.doupdate()


class DetailWindow(Window):
    """
    Window with video info
    """
    target = '~'

    video = None
    stream = None
    streams = False

    def reset(self):
        self.video = None
        self.stream = None
        self.streams = False

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
    class CacheList(OrderedDict):
        """An ordered dictionary of videos"""
        def __init__(self, name):
            super(self.__class__, self).__init__()
            # OrderedDict.__init__(self)
            self.name = name
            self.index = None

    caches = (
        CacheList('Inquiries'),
        CacheList('Downloaded'),
        CacheList('Threads'),
    )
    index = 0
    lookups = caches[0]
    downloads = caches[1]
    threads = caches[2]
    videos = caches[index]

    def reset(self):
        self.caches = (
            self.CacheList('Inquiries'),
            self.CacheList('Downloaded'),
            self.CacheList('Threads'),
        )
        self.index = 0
        self.lookups = self.caches[0]
        self.downloads = self.caches[1]
        self.threads = self.caches[2]
        self.videos = self.caches[self.index]

    def display(self):
        super(ListWindow, self).display()

        self.videos = self.caches[self.index]
        if self.videos == self.threads:
            for thread in threading.enumerate():
                self.threads[thread.name] = thread

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

    def load_lookups(self):
        """ Load file from disk into cache """
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

    def load_downloads(self):
        """ Load file from disk into cache """
        class Cache(): pass

        with open('clipy.downloads', 'r') as f:
            for line in f.readlines():
                url, filename = line.split(maxsplit=1)
                stream = Cache()
                stream.url = url
                self.downloads[url] = Stream(stream, filename.strip())


class Panel(object):
    """docstring for Panel"""
    testing = False

    def __init__(self, stdscr, detail, cache, console):
        self.stdscr = stdscr
        self.detail = detail
        self.cache = cache
        self.console = console

    def reset(self):
        self.detail.reset()
        self.cache.reset()
        self.console.display()

    def display(self):
        self.detail.display()
        self.cache.display()
        self.console.freshen()

    def load_cache(self):
        if os.path.exists('clipy.lookups'):
            self.cache.load_lookups()
            self.console.printstr('Cache: lookups loaded')
        else:
            self.console.printstr('Cache: no lookups found, not loaded')

        if os.path.exists('clipy.downloads'):
            self.cache.load_downloads()
            self.console.printstr('Cache: downloads loaded')
        else:
            self.console.printstr('Cache: no downloads found, not loaded')

    def save_cache(self):
        with open('clipy.lookups', 'w') as f:
            for key in self.cache.lookups:
                cache = self.cache.lookups[key]
                f.write('{} {}\n'.format(cache.video.videoid, cache))

        with open('clipy.downloads', 'w') as f:
            for key in self.cache.downloads:
                cache = self.cache.downloads[key]
                f.write('{} {}\n'.format(cache.stream.url, cache))

            self.console.printstr('Cache: saved')

    # def load_video(self, video):
    #     self.console.printstr('Loading video: {}'.format(video.title))
    #     self.detail.video = video

    #     if self.detail.video.videoid not in self.cache.lookups:
    #         self.cache.lookups[self.detail.video.videoid] = Video(self.detail.video)

    def inquire(self, resource=None):
        if resource is None:
            resource = pyperclip.paste().strip()
            self.console.printstr('Checking clipboard: {}'.format(resource))

        try:
            self.console.printstr('Inquiring: {}'.format(resource))
            self.detail.video = pafy.new(resource)

        except (OSError, ValueError) as e:
            self.console.printstr(e, error=True)

        else:
            # If entry not in Lookups
            if self.detail.video.videoid not in self.cache.lookups:
                # Add entry to Lookups
                vid = self.detail.video.videoid
                self.cache.lookups[vid] = Video(self.detail.video)

    def wait_for_input(self):
        return self.detail.win.getch()

    def view(self, key):
        # Load cache from disk
        if key == ord('L'):
            self.load_cache()

        # Save cache to disk
        elif key == ord('C'):
            self.save_cache()

        # Change cache view
        elif key == curses.KEY_LEFT:
            if self.cache.index > 0:
                self.cache.index -= 1

        # Change cache view
        elif key == curses.KEY_RIGHT:
            if self.cache.index < len(self.cache.caches) - 1:
                self.cache.index += 1

        # Intra-cache navigation
        else:
            # Initialize cache
            if self.cache.videos.index is None:
                self.cache.videos.index = 0
            v_index = self.cache.videos.index

            # Move up the list
            if key == curses.KEY_UP:
                if v_index > 0:
                    self.cache.videos.index -= 1

            # Move down the list
            elif key == curses.KEY_DOWN:
                if v_index < len(self.cache.videos) -1:
                    self.cache.videos.index += 1

            # Selected cache entry action
            elif key == curses.KEY_ENTER or key == 10:

                # Validate selected index
                if v_index >= 0 and v_index < len(self.cache.videos):

                    # Lookups action
                    if self.cache.videos == self.cache.lookups:
                        self.inquire(list(self.cache.videos)[v_index])

                    # Downloads action
                    elif self.cache.videos == self.cache.downloads:
                        key = list(self.cache.videos)[v_index]
                        filename = self.cache.videos[key].filename
                        self.console.printstr('Playing {}'.format(filename))
                        subprocess.call(
                            ['mplayer', "{}".format(filename)],
                            stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL)

    def select(self):
        self.detail.streams = not self.detail.streams

        if self.detail.video:
            if self.detail.streams:
                self.console.printstr(
                    'Press one of the numbers above to download (0-{})'
                    .format(len(self.detail.video.allstreams)-1))
        else:
            self.console.printstr('No video to select streams, Inquire first',
                error=True)

    def cancel(self):
        stream = self.detail.stream

        if stream:
            self.console.printstr('Canceling {} `{}`'.format(stream, stream.title))
            if stream.cancel():
                self.console.printstr('Canceled {} `{}`'.format(stream, stream.title))
        else:
            self.console.printstr('Nothing to cancel')

        self.detail.stream = None

    def progress(self, total, *progress_stats):
        status_string = ('{:,} Bytes [{:.2%}] received. Rate: [{:4.0f} '
                         'KB/s].  ETA: [{:.0f} secs]')
        status = status_string.format(*progress_stats)
        self.stdscr.addstr(0, 15, status, curses.A_REVERSE)
        self.stdscr.noutrefresh()
        curses.doupdate()

    def download(self, index=None):

        def done_callback(stream, filename, success):
            if success:
                self.cache.downloads[stream.url] = Stream(stream, filename)
            self.cache.display()
            self.console.freshen()
            curses.doupdate()

        if self.detail.video is None:
            self.console.printstr('No video to download, Inquire first', error=True)
            return

        if index is None:
            try:
                self.detail.stream = self.detail.video.getbest(preftype="mp4")
            except (OSError, ValueError) as e:
                self.console.printstr(e, error=True)
                return
        else:
            if index >= len(self.detail.video.allstreams):
                self.console.printstr('Stream {} not available'.format(index), error=True)
                return
            self.detail.stream = self.detail.video.allstreams[index]

        t = threading.Thread(
            name=self.detail.video.videoid,
            target=clipy_request_download,
            args=(
                self.detail.stream,
                self.detail.target,
                self.console.printstr,
                self.progress,
                done_callback,
            ))
        t.daemon = True
        t.start()


def loop(stdscr, panel):
    KEYS_NUMERIC  = range(48, 58)
    KEYS_CANCEL   = (ord('x'), ord('X'))
    KEYS_DOWNLOAD = (ord('d'), ord('D'))
    KEYS_INQUIRE  = (ord('i'), ord('I'))
    KEYS_HELP     = (ord('h'), ord('H'))
    KEYS_SELECT   = (ord('s'), ord('S'))
    KEYS_QUIT     = (ord('q'), ord('Q'))
    KEYS_RESET    = (ord('R'),)
    KEYS_CACHE    = (ord('L'), ord('C'), curses.KEY_LEFT, curses.KEY_RIGHT,
        curses.KEY_UP, curses.KEY_DOWN, curses.KEY_ENTER, 10)  # 10 is enter

    while True:

        # Refresh screen
        stdscr.noutrefresh()
        panel.display()
        if not panel.testing:
            curses.doupdate()

        # Blocking
        c = panel.wait_for_input()

        if c in KEYS_QUIT:
            break

        if c in KEYS_RESET:
            panel.reset()

        if c in KEYS_INQUIRE:
            panel.inquire()

        if c in KEYS_SELECT:
            panel.select()

        if c in KEYS_CACHE:
            panel.view(c)

        if c in KEYS_DOWNLOAD:
            panel.download()

        if c in KEYS_NUMERIC:
            panel.download(c-48)

        if c in KEYS_CANCEL:
            panel.cancel()

        if c in KEYS_HELP:
            panel.console.printstr(
                'HELP: Load cache (L), save cache (C) and reset (R) commands '
                'are all upper case only.', wow=True)

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
        ('S', 'streams'),
        ('↑↓', 'cache'),
        ('⏎ ', 'cache'),
        ('L', 'load cache'),
        ('C', 'save cache'),
        ('D', 'download'),
        ('X', 'cancel'),
        ('R', 'reset'),
        ('H', 'help'),
        ('Q', 'quit'),
    )
    menu_string = 'Press: ' + ', '.join(
        ['{}: {}'.format(k, v) for k, v in menu_options])
    stdscr.addstr(curses.LINES-1, 0, menu_string)

    # Create the middle three windows
    detail  = DetailWindow(curses.LINES-9, curses.COLS//2,              1, 0                           )
    cache   = ListWindow  (curses.LINES-9, curses.COLS//2,              1, curses.COLS - curses.COLS//2)
    console = Window      (7             , curses.COLS   , curses.LINES-8, 0                           )
    control_panel = Panel(stdscr, detail, cache, console)

    # Load command line options
    detail.video = video
    detail.stream = stream
    detail.target = target

    # Enter event loop
    loop(stdscr, control_panel)


def main(video=None, stream=None, target=None):
    """
    Single entry point
    """
    curses.wrapper(init, video, stream, target)

if __name__ == '__main__':
    main()
