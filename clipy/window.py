"""
Clipy YouTube video downloader user interface: Window
"""
import os
import re
import curses
import asyncio
import threading
import collections

import clipy.panel
import clipy.video
import clipy.request
import clipy.youtube


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

        if self.panel.input_mode:
            self.printstr('Input your YouTube search string, then press Enter')
            self.printstr('> {}'.format(self.panel.input_text))

        elif self.video:
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
            self.actives or self.CacheList('Active'),
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
                    self.files[path] = clipy.panel.File(filename, path)

        # Threads: manually build the threads list here real-time
        if self.videos is self.threads:
            self.threads.clear()
            for thread in threading.enumerate():
                self.threads[thread.name] = clipy.panel.Thread(thread)

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