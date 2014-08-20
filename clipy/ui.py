"""
Clipy YouTube video downloader user interface
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import re
import curses
import urllib
import asyncio
import functools
import threading
import subprocess
import collections

import pafy
import pyperclip

import clipy.utils
import clipy.request


TITLE = '.:. Clipy .:.'
VERSION = '0.9.7'


class Video(object):
    """Pafy video encapsulation"""
    def __init__(self, video):
        self.video = video

    def __str__(self):
        return '{dur}  {title}'.format(
            dur=self.video.duration, title=self.video.title)


class Stream(object):
    """Pafy stream encapsulation"""
    active = False
    status = None

    def __init__(self, stream, path=None, name=None):
        self.stream = stream
        self.path = path
        self.name = name

    def __str__(self):
        return '{} {}'.format(self.status, self.name or self.stream.title)

    def activate(self):
        self.active = True

    def cancel(self, logger=None):
        self.active = False
        if logger:
            logger('Cancelled {}'.format(self.path))


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
    class CacheList(collections.OrderedDict):
        """An ordered dictionary of videos"""
        def __init__(self, name, title=''):
            super(self.__class__, self).__init__()
            self.index = None
            self.name = name
            self.title = title

        def __str__(self):
            return '{}: {} {}'.format(self.name, len(self), self.title)

    class CacheItem():
        pass

    index = 0
    caches = ()
    lookups = downloads = files = threads = actives = None
    videos = None   # mis-named as videos, s/b cache or something

    def reset(self):
        (self.searches,
         self.lookups,
         self.downloads,
         self.files,
         self.threads,
         self.actives,
        ) = self.caches = (
            self.CacheList('Search'),
            self.CacheList('Inquiries'),
            self.CacheList('Downloaded'),
            self.CacheList('Files', self.panel.target),
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
            target_dir = os.path.expanduser(self.panel.target)
            for filename in sorted(os.listdir(target_dir)):
                path = os.path.join(target_dir, filename)
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
            except Exception:
                break

        self.freshen()

    def load_search(self, url):
        # page = requests.get(resource)
        # tree = html.fromstring(page.text)
        # videos = tree.xpath('//div/@data-context-item-id')

        # r = urllib2.Request(url='http://www.mysite.com')
        # r.add_header('User-Agent', 'Clipy')
        # # r.add_data(urllib.urlencode({'foo': 'bar'})
        # response = urlopen(r)

        self.panel.console.printstr('Searching: {}'.format(url))

        user_agent = 'Mozilla/5.0 (X11; Linux x86_64) Python3 urllib / Clipy'
        headers = {'User-Agent': user_agent}
        request = urllib.request.Request(url, headers=headers)
        # self.panel.console.printstr('Request: {}'.format(request))

        response = urllib.request.urlopen(request)
        html = str(response.read())
        # self.panel.console.printstr('Response: {} {}'.format(len(html), response))

        videoids = re.findall('data-context-item-id="([^"]+)"', html)
        self.panel.console.printstr('Video Ids: {}'.format(videoids))

        if videoids:
            self.searches.clear()
            for videoid in videoids:
                if videoid != '__video_id__':
                    self.searches[videoid] = videoid

    def load_lookups(self):
        """ Load file from disk into cache """
        with open('clipy.lookups', 'r') as f:
            for line in f.readlines():
                key, duration, title = line.split(None, 2)

                video = self.CacheItem()
                video.videoid = key
                video.duration = duration
                video.title = title.strip()

                self.lookups[key] = Video(video)

    def load_downloads(self):
        """ Load file from disk into cache """
        with open('clipy.downloads', 'r') as f:
            for line in f.readlines():

                url, path = line.split(None, 1)
                path = path.strip()

                stream = self.CacheItem()
                stream.url = url
                stream.title = path

                self.downloads[url] = Stream(stream, path)


class Panel(object):
    """docstring for Panel"""
    testing = False
    target = '~'

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
                f.write('{} {}\n'.format(cache.video.videoid, cache))

        with open('clipy.downloads', 'w') as f:
            for key in self.cache.downloads:
                cache = self.cache.downloads[key]
                f.write('{} {}\n'.format(cache.stream.url, cache))

            self.console.printstr('Cache: saved')

    def get_video(self, resource):
        """ Create new Pafy video instance """
        try:
            return pafy.new(resource)
        except (OSError, ValueError) as ex:
            self.console.printstr(ex, error=True)

    @asyncio.coroutine
    def get_video_async(self, resource):
        try:
            return pafy.new(resource)
        except (OSError, ValueError) as ex:
            self.console.printstr(ex, error=True)

    @asyncio.coroutine
    def get_video_homebrew(self, resource):
        try:
            data = yield from clipy.request.get_youtube_info(resource)
        except ConnectionError as ex:
            self.console.printstr(ex, error=True)
            return
        if data is None:
            self.console.printstr('No data returned', error=True)
            return
        self.console.printstr('Got {} bytes as {}'.format(len(data), type(data)))
        # self.console.printstr(data)

        class VideoInner(object):
            def __str__(self):
                return '<<{}>>'.format(self)

        class VideoDetail(object):
            # def __init__(self, video):
            #     self.video = video
            def __str__(self):
                # import pprint
                # p = pprint.pformat(self.info)
                return '''
Id:     {}
Title:  {}
Author: {}
Length: {} seconds
Views:  {}

Streams: {}
                '''.format(
                    clipy.utils.take_first(self.info['video_id']),
                    clipy.utils.take_first(self.info['title']),
                    clipy.utils.take_first(self.info['author']),
                    clipy.utils.take_first(self.info['length_seconds']),
                    clipy.utils.take_first(self.info['view_count']),
                    len(self.info['url_encoded_fmt_stream_map']),
                )
                # with open('qs', 'w') as f:
                #     f.write(output)

            @property
            def videoid(self):
                return clipy.utils.take_first(self.info.get('video_id', None))

        video = VideoInner()
        video.title = '<title>'
        video.videoid = '<videoid>'
        video.duration = '<duration>'

        storage = VideoDetail()
        storage.info = urllib.parse.parse_qs(data)
        storage.video = video

        return storage

    @asyncio.coroutine
    def inquire(self, resource=None):
        video_id = None

        if resource is None:
            resource = pyperclip.paste().strip()
            self.console.printstr('Checking clipboard: {}'.format(resource))

        if len(resource) == 11:
            video_id = resource
        elif 'youtube.com/results?search' in resource:
            self.cache.load_search(resource)
        elif 'youtube.com/watch' in resource:
            video_id = re  # ToDo
        else:
            self.console.printstr('Resource not valid: "{}"'.format(resource), error=True)

        if video_id is None:
            return

        self.console.printstr('Inquiring homeBrew: {}'.format(resource))
        video = yield from self.get_video_homebrew(resource)
        if video:
            self.detail.video = video
            if video.videoid not in self.cache.lookups:
                vid = video.videoid
                self.cache.lookups[vid] = Video(video.video)

        self.display()

    # def inquire(self, resource=None):
    #     # Check if we have a supplied resoure, else check the clipboard
    #     if resource is None:
    #         resource = pyperclip.paste().strip()
    #         self.console.printstr('Checking clipboard: {}'.format(resource))
    #     # We may want to search
    #     if 'youtube.com/results?search' in resource:
    #         self.cache.load_search(resource)
    #     # We can try at YouTube now
    #     else:
    #         self.console.printstr('Inquiring: {}'.format(resource))
    #         video = self.get_video(resource)
    #         if video:
    #             self.detail.video = video
    #             # If entry not in Lookups
    #             if video.videoid not in self.cache.lookups:
    #                 # Add entry to Lookups
    #                 vid = video.videoid
    #                 self.cache.lookups[vid] = Video(video)

    @asyncio.coroutine
    def search(self):
        searches = self.cache.searches
        if searches:
            self.console.printstr('Inquiring on all {} searches'.format(
                len(searches)))
            for videoid in searches:
                video = yield from self.get_video_async(videoid)
                if video:
                    searches[videoid] = Video(video)
                    self.cache.display()
                    self.update()
        else:
            self.console.printstr('No recent searches found, paste search url')

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

            # Selected cache entry action
            elif key == curses.KEY_ENTER or key == 10:

                # Validate selected index
                if v_index >= 0 and v_index < len(self.cache.videos):

                    # Search / Lookups action
                    if self.cache.videos is self.cache.searches or \
                       self.cache.videos is self.cache.lookups:
                        self.inquire(list(self.cache.videos)[v_index])

                    # Downloads action
                    elif self.cache.videos is self.cache.downloads \
                      or self.cache.videos is self.cache.files:
                        key = list(self.cache.videos)[v_index]
                        path = self.cache.videos[key].path
                        self.console.printstr('Playing {}'.format(path))
                        try:
                            subprocess.call(
                                ['mplayer', "{}".format(path)],
                                stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL)
                        except AttributeError:
                            self.console.printstr("Can't play, maybe Python2?")

    def streams(self):
        self.detail.streams = not self.detail.streams

        if self.detail.video:
            if self.detail.streams:
                self.console.printstr(
                    'Press one of the numbers above to download (0-{})'
                    .format(len(self.detail.video.allstreams)-1))
        else:
            self.console.printstr('No video to show streams, Inquire first',
                                  error=True)

    def cancel(self):
        """ Cancel last spawned thread """
        cprint = self.console.printstr
        if self.cache.actives:
            last_key = list(self.cache.actives).pop()
            cprint('Cancelling most recent active download: {}'.format(last_key))
            stream = self.cache.actives[last_key]
            stream.cancel(cprint)
        else:
            cprint('Nothing to cancel')

    @asyncio.coroutine
    def download(self, index=None):
        cprint = self.console.printstr
        target_dir = os.path.expanduser(self.target)

        def progress(url, total, *progress_stats):
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
            if url in self.cache.actives:
                return self.cache.actives[url].active

        def done_callback():
            # Add to downloaded list
            if _length:
                self.cache.downloads[_stream.url] = Stream(_stream, _path)
            # Check if thread not already cancel'd
            if _stream.url in self.cache.actives:
                del self.cache.actives[_stream.url]
            # Update screen to show the active download is no longer active
            self.cache.display()

        if self.detail.video is None:
            cprint('No video to download, Inquire first', error=True)
            return

        if index is None:
            try:
                self.detail.stream = Stream(self.detail.video.getbest(preftype="mp4"))
            except (OSError, ValueError) as e:
                cprint(e, error=True)
                return
        else:
            if index >= len(self.detail.video.allstreams):
                cprint('Stream {} not available'.format(index), error=True)
                return
            self.detail.stream = Stream(self.detail.video.allstreams[index])

        _stream = self.detail.stream.stream

        name = '{}-({}).{}'.format(
            _stream.title, _stream.quality, _stream.extension
            ).replace('/', '|')

        _path = os.path.join(target_dir, name)

        self.console.printstr('Downloading {} `{}` to {}'.format(
            _stream, _stream.title, target_dir))

        self.cache.actives[_stream.url] = Stream(_stream, _path)
        self.cache.actives[_stream.url].activate()

        _length = yield from clipy.request.download(
            _stream.url,
            path=_path,
            active_poll=functools.partial(active_poll, _stream.url),
            progress_callback=progress,
        )

        done_callback()

        self.console.printstr('Apparently {} bytes were saved to {}.'.format(
            _length, _path))


def key_loop(stdscr, panel):
    KEYS_NUMERIC  = range(48, 58)
    KEYS_DOWNLOAD = (ord('d'), ord('D'))
    KEYS_INQUIRE  = (ord('i'), ord('I'))
    KEYS_SEARCH   = (ord('s'), ord('S'))
    KEYS_HELP     = (ord('h'), ord('H'))
    KEYS_STREAMS  = (ord('v'), ord('V'))
    KEYS_QUIT     = (ord('q'), ord('Q'))
    KEYS_RESET    = (ord('R'),)
    KEYS_CANCEL   = (ord('X'),)
    KEYS_CACHE    = (ord('L'), ord('C'), curses.KEY_LEFT, curses.KEY_RIGHT,
        curses.KEY_UP, curses.KEY_DOWN, curses.KEY_ENTER, 10)  # 10 is enter

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

        # Debug
        if c in (ord('Z'),):
            panel.loop.call_soon_threadsafe(asyncio.async, panel.inquire('g79HokJTfPU'))

        if c in KEYS_INQUIRE:
            panel.loop.call_soon_threadsafe(asyncio.async, panel.inquire())

        if c in KEYS_SEARCH:
            panel.loop.call_soon_threadsafe(asyncio.async, panel.search())

        if c in KEYS_DOWNLOAD:
            panel.loop.call_soon_threadsafe(asyncio.async, panel.download())

        if c in KEYS_STREAMS:
            panel.streams()

        if c in KEYS_CACHE:
            panel.view(c)

        if c in KEYS_NUMERIC:
            panel.download(c-48)

        if c in KEYS_CANCEL:
            panel.cancel()

        if c in KEYS_HELP:
            panel.console.printstr(
                'HELP: Load cache (L), save cache (C), reset (R) and cancel (X)'
                ' commands are all upper case only.', wow=True)

        # Debug
        stdscr.addstr(
            curses.LINES-1, curses.COLS-20,
            'c={}, t={}      '.format(c, threading.active_count()))


def init(stdscr, loop, video, stream, target):

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
        ('S', 'search'),
        ('V', 'streams'),
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
    detail.video = video
    detail.stream = Stream(stream)
    control_panel.target = target

    # Enter curses keyboard event loop
    key_loop(stdscr, control_panel)
    loop.call_soon_threadsafe(loop.stop)


def main(video=None, stream=None, target=None):
    """
    Single entry point
    """
    # Python event loop
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_in_executor(None, curses.wrapper, *(init, loop, video, stream, target))
    loop.run_forever()
    loop.close()

if __name__ == '__main__':
    main()
