"""
Clipy YouTube video downloader user interface: Panel
"""
import os
import curses
import asyncio
import subprocess

import pyperclip

import clipy.request
import clipy.youtube


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


class Panel(object):
    """docstring for Panel"""
    testing = False
    target_dir = ''
    input_mode = False
    input_text = ''

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
        cprint = self.console.printstr

        if os.path.exists('clipy.lookups'):
            self.cache.load_lookups()
            cprint('Cache: lookups loaded')
        else:
            cprint('Cache: no lookups found, not loaded')

        if os.path.exists('clipy.downloads'):
            self.cache.load_downloads()
            cprint('Cache: downloads loaded')
        else:
            cprint('Cache: no downloads found, not loaded')

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
    def clipboard(self):
        cprint = self.console.printstr
        try:
            contents = pyperclip.paste()
        except:
            contents = None
            cprint('Cannot seem to read the clipboad, try (I) input')
        if contents:
            contents = str(contents).strip()
            cprint('Checking clipboard: {}'.format(contents))
            yield from self.inquire(contents)
        else:
            cprint('Found nothing in clipboard')

    @asyncio.coroutine
    def inquire(self, resource):
        cprint = self.console.printstr

        if 'youtube.com/results?search' in resource:
            yield from self.cache.load_search(resource)
            return

        cprint('Inquiring: {}'.format(resource))
        try:
            video = yield from clipy.youtube.get_video(
                resource, target=self.target_dir)

        except ValueError as ex:
            cprint('Error: {}'.format(ex), error=True)

        except ConnectionError as ex:
            cprint('Error: {}'.format(ex), error=True)

        else:
            if video:
                self.detail.video = video
                self.cache.lookups[video.videoid] = video
                self.cache.streams.index = None
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
        """ The Enter key was pressed """
        cprint = self.console.printstr

        # If we are in input mode then just inquire
        if self.input_mode:
            self.input_mode = False
            yield from self.inquire(self.input_text)
            return

        def play():
            cprint('Playing {}'.format(path))
            try:
                subprocess.call(
                    ['mplayer', "{}".format(path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL)
            except AttributeError:
                cprint("Can't play, Python2?")

        v_index = self.cache.videos.index

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
                    if os.path.exists(path):
                        self.loop.run_in_executor(None, play)
                    else:
                        cprint('File no longer exists {}'.format(path),
                               error=True)

                # Actives action
                elif self.cache.videos is self.cache.actives:
                    try:
                        key = list(self.cache.actives)[v_index]
                        cprint('Cancelling download: {}'.format(
                            self.cache.actives[key]))
                        del self.cache.actives[key]
                    except IndexError:
                        cprint('Nothing to cancel')

    @asyncio.coroutine
    def download(self, video, index=None):
        cprint = self.console.printstr

        if video is None:
            cprint('No video to download, Inquire first', error=True)
            return

        stream = video.stream = video.streams[index or 0]

        if stream.url in self.cache.actives:
            cprint('Stream already downloading: {}'.format(stream))
            return

        cprint('Downloading {}'.format(stream.path))

        self.cache.actives[stream.url] = stream

        _success, _length = yield from clipy.request.governed_download(
            stream, self.cache.actives)

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
