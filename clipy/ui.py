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

import pyperclip

import clipy.utils
import clipy.request


TITLE = '.:. Clipy .:.'
VERSION = '0.9.12'

# Borrowed from Pafy https://github.com/np1/pafy
ITAGS = {
    '5': ('320x240', 'flv', "normal", ''),
    '17': ('176x144', '3gp', "normal", ''),
    '18': ('640x360', 'mp4', "normal", ''),
    '22': ('1280x720', 'mp4', "normal", ''),
    '34': ('640x360', 'flv', "normal", ''),
    '35': ('854x480', 'flv', "normal", ''),
    '36': ('320x240', '3gp', "normal", ''),
    '37': ('1920x1080', 'mp4', "normal", ''),
    '38': ('4096x3072', 'mp4', "normal", '4:3 hi-res'),
    '43': ('640x360', 'webm', "normal", ''),
    '44': ('854x480', 'webm', "normal", ''),
    '45': ('1280x720', 'webm', "normal", ''),
    '46': ('1920x1080', 'webm', "normal", ''),

    # '59': ('1x1', 'mp4', 'normal', ''),
    # '78': ('1x1', 'mp4', 'normal', ''),

    '82': ('640x360-3D', 'mp4', "normal", ''),
    '83': ('640x480-3D', 'mp4', 'normal', ''),
    '84': ('1280x720-3D', 'mp4', "normal", ''),
    '100': ('640x360-3D', 'webm', "normal", ''),
    '102': ('1280x720-3D', 'webm', "normal", ''),
    '133': ('426x240', 'm4v', 'video', ''),
    '134': ('640x360', 'm4v', 'video', ''),
    '135': ('854x480', 'm4v', 'video', ''),
    '136': ('1280x720', 'm4v', 'video', ''),
    '137': ('1920x1080', 'm4v', 'video', ''),
    '138': ('4096x3072', 'm4v', 'video', ''),
    '139': ('48k', 'm4a', 'audio', ''),
    '140': ('128k', 'm4a', 'audio', ''),
    '141': ('256k', 'm4a', 'audio', ''),
    '160': ('256x144', 'm4v', 'video', ''),
    '167': ('640x480', 'webm', 'video', ''),
    '168': ('854x480', 'webm', 'video', ''),
    '169': ('1280x720', 'webm', 'video', ''),
    '170': ('1920x1080', 'webm', 'video', ''),
    '171': ('128k', 'ogg', 'audio', ''),
    '172': ('192k', 'ogg', 'audio', ''),
    '218': ('854x480', 'webm', 'video', 'VP8'),
    '219': ('854x480', 'webm', 'video', 'VP8'),
    '242': ('360x240', 'webm', 'video', 'VP9'),
    '243': ('480x360', 'webm', 'video', 'VP9'),
    '244': ('640x480', 'webm', 'video', 'VP9'),
    '245': ('640x480', 'webm', 'video', 'VP9'),
    '246': ('640x480', 'webm', 'video', 'VP9'),
    '247': ('720x480', 'webm', 'video', 'VP9'),
    '248': ('1920x1080', 'webm', 'video', 'VP9'),
    '256': ('192k', 'm4a', 'audio', '6-channel'),
    '258': ('320k', 'm4a', 'audio', '6-channel'),
    '264': ('2560x1440', 'm4v', 'video', ''),
    '271': ('1920x1280', 'webm', 'video', 'VP9'),
    '272': ('3414x1080', 'webm', 'video', 'VP9')
}


class VideoDetail(object):
    info = dict()
    stream = None
    streams =list()
    info_map = dict(
        videoid='video_id',
        duration='length_seconds',
    )

    def __init__(self, data=None):
        if data is not None:
            # data is url querystring format, so we need to parse it
            self.info = urllib.parse.parse_qs(data)

            # first we split the mapping on the commas
            stream_map = clipy.utils.take_first(
                self.info.get('url_encoded_fmt_stream_map', ())).split(',')

            # then we zip/map the values into our streams list
            self.streams = [{k: clipy.utils.take_first(v)
                for k, v in sdic.items()}
                for sdic in [urllib.parse.parse_qs(mapp)
                for mapp in stream_map]]

            # now add in our new fields
            for stream in self.streams:

                itags = [t for t in ITAGS.get(stream.get('itag', None)) if t]

                display = '{} ({}) {}'.format(
                    ', '.join(itags),
                    stream.get('quality', 'unknown'),
                    stream.get('type', ''))

                stream.update(dict(
                    display=display,
                    resolution=itags[0]),
                    extension=itags[1],
                )

            # from pprint import pformat
            # info = pformat(self.info)
            # strm = pformat(self.streams)
            # with open('INIT', 'w') as f:
            #     f.write('data: '); f.write(data); f.write('\n\n')
            #     f.write('info: '); f.write(info); f.write('\n\n')
            #     f.write('stream_map: '); f.write(str(stream_map)); f.write('\n\n')
            #     f.write('strm: '); f.write(strm); f.write('\n\n')
            #     f.write('------------------------------------\n\n')

    def __getattr__(self, name):
        """
        Check if our attribute exists for the object, otherwise return the
        corresponding entry from our 'info'.
        """
        # from pprint import pformat
        # print('!!!!!!!!!', name)
        # # import pdb; pdb.set_trace()
        # sdict = pformat(self.__dict__)
        # dname = self.__dict__.get(name, '?.')
        # mname = self.info_map.get(name, name)
        # ninfo = self.info.get(mname)
        # finfo = clipy.utils.take_first(ninfo)
        # with open('getattr.{}'.format(name), 'w') as f:
        #     f.write('name:  '); f.write(     name ); f.write('\n\n')
        #     f.write('dict:  '); f.write(    sdict ); f.write('\n\n')
        #     f.write('dname: '); f.write(    dname ); f.write('\n\n')
        #     f.write('mname: '); f.write(    mname ); f.write('\n\n')
        #     f.write('ninfo: '); f.write(str(ninfo)); f.write('\n\n')
        #     f.write('finfo: '); f.write(    finfo ); f.write('\n\n')
        return self.__dict__.get(name,
            clipy.utils.take_first(
               self.info.get(
                    self.info_map.get(name, name))))

    def __str__(self):
        return '> {duration}  {title}  {path}'.format(
            duration=self.duration, title=self.title, path=self.path)

    @property
    def detail(self):
        # import pprint
        # p = pprint.pformat(self.info)
        return '''
Id:     {}
Title:  {}
Author: {}
Length: {} seconds
Views:  {}

Streams: {}
* {}
        '''.format(
            clipy.utils.take_first(self.info['video_id']),
            clipy.utils.take_first(self.info['title']),
            clipy.utils.take_first(self.info['author']),
            clipy.utils.take_first(self.info['length_seconds']),
            clipy.utils.take_first(self.info['view_count']),
            len(self.streams),
            '\n* '.join([stream['display'] for stream in self.streams]),
        )
        # with open('qs', 'w') as f:
        #     f.write(output)


class Stream(VideoDetail):
    """Video stream """
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
            self.printstr(self.video.detail)

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
                    video = yield from self.panel.get_video(videoid)
                    if video:
                        self.searches[videoid] = video
                        self.display()
                        self.panel.update()

    def load_lookups(self):
        """ Load file from disk into cache """
        with open('clipy.lookups', 'r') as f:
            for line in f.readlines():
                key, duration, title = line.split(None, 2)

                video = VideoDetail()
                video.videoid = key
                video.duration = duration
                video.title = title.strip()

                self.lookups[key] = video

    def load_downloads(self):
        """ Load file from disk into cache """
        with open('clipy.downloads', 'r') as f:
            for line in f.readlines():

                url, path = line.split(None, 1)
                path = path.strip()

                stream = VideoDetail()
                stream.url = url
                stream.path = path

                self.downloads[url] = stream


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
                f.write('{} {}\n'.format(cache.videoid, cache))

        with open('clipy.downloads', 'w') as f:
            for key in self.cache.downloads:
                cache = self.cache.downloads[key]
                f.write('{} {}\n'.format(cache.stream.url, cache))

            self.console.printstr('Cache: saved')

    @asyncio.coroutine
    def get_video(self, resource):
        try:
            data = yield from clipy.request.get_youtube_info(resource)
        except ConnectionError as ex:
            self.console.printstr(ex, error=True)
            return
        if data is None:
            self.console.printstr('No data returned', error=True)
            return

        return VideoDetail(data)

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
        video = yield from self.get_video(resource)
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
                    # print(' View() list caches.videos: {}'.format(list(self.cache.videos)))
                    # print(' View() index caches.videos: {}'.format(list(self.cache.videos)[v_index]))
                    yield from self.inquire(list(self.cache.videos)[v_index])

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
                        self.console.printstr("Can't play, Python2?")

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
    def download(self, video, index=None):
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

        if video is None:
            cprint('No video to download, Inquire first', error=True)
            return

        _stream = video.stream = video.streams[index or 0]

        name = '{}-({}).{}'.format(
            self.detail.video.title, _stream['resolution'], _stream['extension']
            ).replace('/', '|')

        _path = os.path.join(target_dir, name)

        cprint('Downloading {}'.format(_path))

        self.cache.actives[_stream['url']] = Stream(_stream, _path, name)
        self.cache.actives[_stream['url']].activate()

        # here is the magic goodness
        _success, _length = yield from clipy.request.download(
            _stream['url'],
            path=_path,
            active_poll=functools.partial(active_poll, _stream['url']),
            progress_callback=progress,
        )
        # and here we start our inline that would "normally" be in a callback

        # Add to downloaded list
        if _success:
            self.cache.downloads[_stream['url']] = Stream(_stream, _path)

        # Check if thread not already cancel'd
        if _stream['url'] in self.cache.actives:
            del self.cache.actives[_stream['url']]

        # Update screen to show the active download is no longer active
        self.cache.display()
        cprint('Perhaps {} bytes were saved to {}'.format(_length, _path))


def key_loop(stdscr, panel):
    KEYS_NUMERIC  = range(48, 58)
    KEYS_DOWNLOAD = (ord('d'), ord('D'))
    KEYS_INQUIRE  = (ord('i'), ord('I'))
    KEYS_STREAMS  = (ord('s'), ord('S'))
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

        # if c in KEYS_SEARCH:
        #     panel.loop.call_soon_threadsafe(asyncio.async, panel.search())

        if c in KEYS_DOWNLOAD:
            panel.loop.call_soon_threadsafe(asyncio.async, panel.download(panel.detail.video))

        if c in KEYS_ACTION:
            panel.loop.call_soon_threadsafe(asyncio.async, panel.action())

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
        if c in (ord('Z'),):
            panel.loop.call_soon_threadsafe(asyncio.async, panel.inquire('g79HokJTfPU'))

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
        ('S', 'streams'),
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
