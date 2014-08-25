"""
Clipy YouTube video downloader user interface
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import re
import curses
import asyncio
import functools
import threading
import subprocess
import collections

import pyperclip

import clipy.video
import clipy.request
import clipy.youtube

TITLE = '.:. Clipy .:.'
VERSION = '0.9.18'


class File(object):
    """file encapsulation"""
    def __init__(self, name, path):
        self.name = name
        self.path = path

    def __str__(self):
        return str(self.name)


class Thread(object):
    """thread encapsulation"""
    def __init__(self, thread):
        self.thread = thread
        self.name = thread.name

    def __str__(self):
        return str('{}: ident {}, {}'.format(
            self.name,
            self.thread.ident,
            'Alive' if self.thread.is_alive() else 'Dead',
            'Daemon' if self.thread.daemon else '',
        ))


class Window(object):
    """
    Window absraction with border
    """
    win = box = None
    panel = None

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
        self.panel.update()


class DetailWindow(Window):
    """
    Window with video info
    """
    video = None

    def reset(self):
        self.video = None

    def display(self):
        super(DetailWindow, self).display()

        if self.video:
            self.printstr(self.video.detail)
            self.panel.cache.streams.clear()
            for stream in self.video.streams:
                self.panel.cache.streams[stream.url] = stream

        self.freshen()


class ListWindow(Window):
    """
    Window with cache storage and list capabilities
    """
    class CacheList(collections.OrderedDict):
        """An ordered dictionary of videos"""
        def __init__(self, name, title=''):
            super(self.__class__, self).__init__()
            self.index = None
            self.name = name
            self.title = title

        def __str__(self):
            return '{}: {} {}'.format(self.name, len(self), self.title)

    index = 0
    caches = ()
    searches = lookups = streams = downloads = files = threads = actives = None
    videos = None   # mis-named as videos, s/b cache or something

    def reset(self):
        (
            self.searches,
            self.lookups,
            self.streams,
            self.downloads,
            self.files,
            self.threads,
            self.actives,

        ) = self.caches = (

            self.CacheList('Search'),
            self.CacheList('Inquiries'),
            self.CacheList('Streams'),
            self.CacheList('Downloaded'),
            self.CacheList('Files', self.panel.target_dir),
            self.CacheList('Threads'),
            self.CacheList('Active'),
        )
        self.index = 0
        self.videos = self.caches[self.index]

    def display(self):
        super(ListWindow, self).display()

        # Setup our videos pointer
        self.videos = self.caches[self.index]

        # Files: manually build the files list here real-time
        if self.videos is self.files:
            self.files.clear()
            for filename in sorted(os.listdir(self.panel.target_dir)):
                path = os.path.join(self.panel.target_dir, filename)
                if os.path.isfile(path) and not filename.startswith('.'):
                    self.files[path] = File(filename, path)

        # Threads: manually build the threads list here real-time
        if self.videos is self.threads:
            self.threads.clear()
            for thread in threading.enumerate():
                self.threads[thread.name] = Thread(thread)

        # Header: Display list of caches
        for i, cache in enumerate(self.caches):
            attr = curses.A_STANDOUT if cache.name == self.videos.name else 0
            self.win.addstr(' {} '.format(cache.name.upper()), attr)

        # Rows: Display selected cache detail
        self.win.addstr(2, 2, str(self.videos))
        for i, key in enumerate(self.videos):
            video = self.videos[key]
            attr = curses.A_STANDOUT if i == self.videos.index else 0
            try:
                self.win.addstr(3+i, 0, str(video), attr)
            except Exception:  # Python 3 -> except:
                break

        self.freshen()

    @asyncio.coroutine
    def load_search(self, url):
        self.panel.console.printstr('Searching: {}'.format(url))
        html = yield from clipy.request.get_text(url)
        videoids = re.findall('data-context-item-id="([^"]+)"', html)
        self.panel.console.printstr('Video Ids: {}'.format(videoids))

        if videoids:
            self.searches.clear()
            for videoid in videoids:
                if videoid != '__video_id__':
                    video = yield from clipy.youtube.get_video(
                        videoid, target=self.panel.target_dir)
                    if video:
                        self.searches[videoid] = video
                        self.display()
                        self.panel.update()

    def load_lookups(self):
        """ Load file from disk into cache """
        with open('clipy.lookups', 'r') as f:
            for line in f.readlines():
                key, duration, title = line.split(maxsplit=2)

                video = clipy.video.VideoDetail()
                video.videoid = key
                video.duration = duration
                video.title = title.strip()

                self.lookups[key] = video

    def load_downloads(self):
        """ Load file from disk into cache """
        with open('clipy.downloads', 'r') as f:
            for line in f.readlines():
                stream = clipy.video.VideoDetail()
                stream.url, stream.path = line.split(maxsplit=1)
                stream.path = stream.path.strip()
                self.downloads[stream.url] = stream


class Panel(object):
    """docstring for Panel"""
    testing = False
    target_dir = ''

    def __init__(self, loop, stdscr, detail, cache, console):
        self.loop = loop
        self.stdscr = stdscr
        self.detail = detail
        self.cache = cache
        self.console = console
        # Should be in respective inits
        detail.panel = cache.panel = console.panel = self
        cache.win.scrollok(False)
        cache.reset()

    def reset(self):
        self.detail.reset()
        self.cache.reset()
        self.console.display()

    def display(self):
        self.detail.display()
        self.cache.display()
        self.console.freshen()
        self.update()

    def update(self):
        if not self.testing:
            curses.doupdate()

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
                f.write('{} {}\n'.format(cache.videoid, cache))

        with open('clipy.downloads', 'w') as f:
            for key in self.cache.downloads:
                cache = self.cache.downloads[key]
                f.write('{} {}\n'.format(cache.stream.url, cache))

            self.console.printstr('Cache: saved')

    @asyncio.coroutine
    def inquire(self, resource=None):
        video_id = None

        if resource is None:
            resource = pyperclip.paste().strip()
            self.console.printstr('Checking clipboard: {}'.format(resource))

        if len(resource) == 11:
            video_id = resource
        elif 'youtube.com/results?search' in resource:
            yield from self.cache.load_search(resource)
        elif 'youtube.com/watch' in resource:
            video_id = re  # ToDo
        else:
            self.console.printstr('Resource not valid: "{}"'.format(resource), error=True)

        if video_id is None:
            return

        self.console.printstr('Inquiring: {}'.format(resource))
        video = yield from clipy.youtube.get_video(resource, target=self.target_dir)
        if video:
            self.detail.video = video
            self.cache.lookups[video.videoid] = video

        self.display()

    def wait_for_input(self):
        # self.cache.win.nodelay(False)
        return self.cache.win.getch()

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
            v_index = self.cache.videos.index

            # Move up the list
            if key == curses.KEY_UP:
                if v_index is None:
                    self.cache.videos.index = 0
                elif v_index > 0:
                    self.cache.videos.index -= 1

            # Move down the list
            elif key == curses.KEY_DOWN:
                if v_index is None:
                    self.cache.videos.index = 0
                elif v_index < len(self.cache.videos) - 1:
                    self.cache.videos.index += 1

    @asyncio.coroutine
    def action(self):
        v_index = self.cache.videos.index
        # print(' View() v_index: {}'.format(v_index))

        if v_index is not None:
            # Validate selected index
            if v_index >= 0 and v_index < len(self.cache.videos):

                # Search / Lookups action
                if self.cache.videos is self.cache.searches or \
                   self.cache.videos is self.cache.lookups:
                    yield from self.inquire(list(self.cache.videos)[v_index])

                # Streams action
                elif self.cache.videos is self.cache.streams:
                    yield from self.download(self.detail.video, v_index)

                # Downloads action
                elif self.cache.videos is self.cache.downloads \
                  or self.cache.videos is self.cache.files:
                    key = list(self.cache.videos)[v_index]
                    path = self.cache.videos[key].path
                    if not os.path.exists(path):
                        self.console.printstr('File no longer exists {}'.format(
                            path), error=True)
                    else:
                        self.console.printstr('Playing {}'.format(path))
                        try:
                            subprocess.call(
                                ['mplayer', "{}".format(path)],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
                        except AttributeError:
                            self.console.printstr("Can't play, Python2?")

    def cancel(self):
        """ Cancel last spawned thread """
        cprint = self.console.printstr
        if self.cache.actives:
            last_key = list(self.cache.actives).pop()
            cprint('Cancelling most recent active download: {}'.format(
                self.cache.actives[last_key]))
            del self.cache.actives[last_key]
        else:
            cprint('Nothing to cancel')

    @asyncio.coroutine
    def download(self, video, index=None):
        cprint = self.console.printstr

        if video is None:
            cprint('No video to download, Inquire first', error=True)
            return

        def progress_poll(url, total, *progress_stats):
            """" The downloader will poll this after each chunk """
            # Build status string
            status_string = (
                '({total}) {:,} Bytes ({:.0%}) @ {:.0f} KB/s, ETA: {:.0f} secs  ')
            status = status_string.format(*progress_stats, total=total)

            # Update main screen status
            self.stdscr.addstr(0, 15, status, curses.A_REVERSE)
            self.stdscr.noutrefresh()

            # Update actives status
            if url in self.cache.actives:  # may have been cancelled
                self.cache.actives[url].status = status
                self.cache.display()

            # Commit screen changes
            self.update()

        def active_poll(url):
            """" The downloader will poll this after each chunk """
            return url in self.cache.actives

        # get the stream we want
        stream = video.stream = video.streams[index or 0]

        cprint('Downloading {}'.format(stream.path))

        # add to actives list
        self.cache.actives[stream.url] = stream

        # here is the magic goodness
        _success, _length = yield from clipy.request.download(
            stream,
            active_poll=active_poll,
            progress_poll=progress_poll,
        )
        # and here we start our inline that would "normally" be in a callback

        # Add to downloaded list
        if _success:
            self.cache.downloads[stream.url] = stream

        # Remove from actives list if not already cencelled
        if stream.url in self.cache.actives:
            del self.cache.actives[stream.url]

        # Update screen to show the active download is no longer active
        self.cache.display()
        cprint('Perhaps {} bytes were saved to {}'.format(_length, stream.path))


def key_loop(stdscr, panel):
    KEYS_DOWNLOAD = (ord('d'), ord('D'))
    KEYS_INQUIRE  = (ord('i'), ord('I'))
    KEYS_HELP     = (ord('h'), ord('H'))
    KEYS_QUIT     = (ord('q'), ord('Q'))
    KEYS_RESET    = (ord('R'),)
    KEYS_CANCEL   = (ord('X'),)
    KEYS_CACHE    = (ord('L'), ord('C'), curses.KEY_LEFT, curses.KEY_RIGHT,
                     curses.KEY_UP, curses.KEY_DOWN)
    KEYS_ACTION   = (curses.KEY_ENTER, 10)  # 10 is enter

    while True:

        # Refresh screen
        stdscr.noutrefresh()
        panel.display()

        # Accept keyboard input
        c = panel.wait_for_input()

        if c in KEYS_QUIT:
            break

        if c in KEYS_RESET:
            panel.reset()

        if c in KEYS_INQUIRE:
            panel.loop.call_soon_threadsafe(asyncio.async, panel.inquire())

        if c in KEYS_DOWNLOAD:
            panel.loop.call_soon_threadsafe(asyncio.async, panel.download(
                panel.detail.video))

        if c in KEYS_ACTION:
            panel.loop.call_soon_threadsafe(asyncio.async, panel.action())

        if c in KEYS_CACHE:
            panel.view(c)

        if c in KEYS_CANCEL:
            panel.cancel()

        if c in KEYS_HELP:
            panel.console.printstr(
                'HELP: Load cache (L), save cache (C), reset (R) and cancel (X)'
                ' commands are all upper case only.', wow=True)

        # Debug
        if c in (ord('Z'),):
            panel.loop.call_soon_threadsafe(asyncio.async, panel.inquire('g79HokJTfPU'))

        # Debug
        stdscr.addstr(
            curses.LINES-1, curses.COLS-20,
            'c={}, t={}      '.format(c, threading.active_count()))


def init(stdscr, loop, resource, target):

    # Setup curses
    curses.curs_set(False)
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
    if curses.has_colors():
        curses.start_color()

    # Title bar at top
    stdscr.addstr(TITLE, curses.A_REVERSE)
    stdscr.chgat(-1, curses.A_REVERSE)
    version = 'UIv {} '.format(VERSION)
    stdscr.addstr(0, curses.COLS-len(version), version, curses.A_REVERSE)

    # Menu options at bottom
    menu_options = (
        ('I', 'inquire'),
        ('arrows', 'cache'),
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
    control_panel = Panel(loop, stdscr, detail, cache, console)

    # Load command line options
    control_panel.target_dir = os.path.expanduser(target)
    if resource:
        stdscr.noutrefresh()
        loop.call_soon_threadsafe(asyncio.async, control_panel.inquire(resource))

    # Enter curses keyboard event loop
    key_loop(stdscr, control_panel)
    loop.call_soon_threadsafe(loop.stop)


def main(resource=None, target=None):
    """
    Single entry point to run two event loops:

    1. Python `asyncio` event loop
    2. Curses wrapper runs init in another thread which in-turn runs `key_loop`
    """
    # Python event loop
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_in_executor(None, curses.wrapper, *(init, loop, resource, target))
    loop.run_forever()
    loop.close()

if __name__ == '__main__':
    main()
