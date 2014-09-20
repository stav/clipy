"""
Clipy YouTube video downloader user interface: Panel
"""
import os
import curses
import asyncio
import logging
import subprocess

import pyperclip

import clipy.youtube
import clipy.download

logger = logging.getLogger('clipy')


class BasePanel(object):
    """ Synchronous panel code """
    testing = False
    target_dir = ''

    def __init__(self, loop, stdscr, detail, cache, console, popup):
        self.loop = loop
        self.stdscr = stdscr
        self.detail = detail
        self.cache = cache
        self.console = console
        self.popup = popup

        # Recursive attributes
        detail.panel = cache.panel = console.panel = popup.panel = self

        # Should be in window.ListWindow.__init__
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

    def wait_for_input(self):
        # self.cache.win.nodelay(False)
        return self.cache.win.getch()

    def load_cache(self):
        if os.path.exists('clipy.lookups'):
            self.cache.load_lookups()
            logger.info('Cache: lookups loaded')
        else:
            logger.warn('Cache: no lookups found, not loaded')

        if os.path.exists('clipy.downloads'):
            self.cache.load_downloads()
            logger.info('Cache: downloads loaded')
        else:
            logger.warn('Cache: no downloads found, not loaded')

    def save_cache(self):
        with open('clipy.lookups', 'w') as f:
            for key in self.cache.lookups:
                cache = self.cache.lookups[key]
                f.write('{} {}\n'.format(cache.videoid, cache))

        with open('clipy.downloads', 'w') as f:
            for key in self.cache.downloads:
                cache = self.cache.downloads[key]
                f.write('{} {}\n'.format(cache.stream.url, cache))

        logger.info('Cache: saved')

    def view_left(self):
        # Change cache view one tab to the left
        if self.cache.index > 0:
            self.cache.index -= 1

    def view_right(self):
        # Change cache view one tab to the right
        if self.cache.index < len(self.cache.caches) - 1:
            self.cache.index += 1

    def view_up(self):
        v_index = self.cache.videos.index
        # Move up the list
        if v_index is None:
            self.cache.videos.index = 0
        elif v_index > 0:
            self.cache.videos.index -= 1

    def view_down(self):
        v_index = self.cache.videos.index
        # Move down the list
        if v_index is None:
            self.cache.videos.index = 0
        elif v_index < len(self.cache.videos) - 1:
            self.cache.videos.index += 1


class Panel(BasePanel):
    """ Asynchronous panel code """

    @asyncio.coroutine
    def clipboard(self):
        try:
            contents = pyperclip.paste()
        except:
            contents = None
            logger.warn('Cannot seem to read the clipboad, try input (I)')

        if contents:
            contents = str(contents).strip()
            logger.info('Checking clipboard: {}'.format(contents))
            yield from self.inquire(contents)
        else:
            logger.info('Found nothing in clipboard')

    @asyncio.coroutine
    def inquire(self, resource):
        if 'youtube.com/results?' in resource:
            yield from self.cache.load_search(resource)
            return

        if resource:
            logger.info('Inquiring: {}'.format(resource))
            try:
                video = yield from clipy.youtube.get_video(
                    resource, target=self.target_dir)

            except (ConnectionError, ValueError) as ex:
                logger.error(ex)

            else:
                if video:
                    self.detail.video = video
                    self.cache.lookups[video.videoid] = video
                    self.cache.streams.index = None
                    self.cache.streams.clear()

                    # Add our video streams to the cache
                    for stream in video.streams:
                        if hasattr(stream, 'url'):
                            self.cache.streams[stream.url] = stream
                        else:
                            logger.warn('Stream does not have a url: {}'.format(stream))

                    self.display()

    @asyncio.coroutine
    def action(self):
        """
        The Enter key was pressed

        * Search  action: Inquire
        * Lookups action: Inquire
        * Streams action: Download
        * Files   action: Play
        * Threads action: Print
        * actives action: Cancel
        """
        def play():
            logger.info('Playing {}'.format(path))
            try:
                subprocess.call(
                    ['mplayer', "{}".format(path)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL)

            except FileNotFoundError as ex:
                logger.error("Can't play: {}".format(ex))

        v_index = self.cache.videos.index

        if v_index is not None:
            # Validate selected index
            if v_index >= 0 and v_index < len(self.cache.videos):

                # Search / Lookups action: inquire
                if self.cache.videos is self.cache.searches or \
                   self.cache.videos is self.cache.lookups:
                    yield from self.inquire(list(self.cache.videos)[v_index])

                # Streams action: download
                elif self.cache.videos is self.cache.streams:
                    yield from self.download(self.detail.video, v_index)

                # Files action: play
                elif self.cache.videos is self.cache.downloads \
                  or self.cache.videos is self.cache.files:
                    key = list(self.cache.videos)[v_index]
                    path = self.cache.videos[key].path
                    if os.path.exists(path):
                        self.loop.run_in_executor(None, play)
                    else:
                        logger.error('File no longer exists {}'.format(path))

                # Threads action: console print
                elif self.cache.videos is self.cache.threads:
                    key = list(self.cache.videos)[v_index]
                    thread = self.cache.videos[key]
                    logger.info(thread)

                # Actives action: cancel
                elif self.cache.videos is self.cache.actives:
                    try:
                        key = list(self.cache.actives)[v_index]
                        logger.info('Cancelling download: {}'.format(
                            self.cache.actives[key]))
                        del self.cache.actives[key]
                    except IndexError:
                        logger.warn('Nothing to cancel')

    @asyncio.coroutine
    def _download(self, video, index):
        stream = video.stream = video.streams[index]

        if stream.url in self.cache.actives:
            logger.warn('Stream already downloading: {}'.format(stream))
            return

        logger.debug('Preparing to download {}'.format(stream.path))

        self.cache.actives[stream.url] = stream

        try:
            _success, _length = yield from clipy.download.get(
                stream, self.cache.actives)

        except ConnectionError as ex:
            logger.error(ex)

        # and here we start our inline that would "normally" be in a callback

        else:
            # Add to downloaded list
            if _success:
                self.cache.downloads[stream.url] = stream

            # Update screen to show the active download is no longer active
            self.cache.display()
            logger.info('Perhaps {} bytes were saved to {}'.format(_length, stream.path))

        finally:
            # Remove from actives list if not already cencelled
            if stream.url in self.cache.actives:
                del self.cache.actives[stream.url]

    @asyncio.coroutine
    def download(self, video, index=None):
        """
        Request download of specified video

        If no stream index provided then download all streams.
        """
        if video is None:
            logger.warn('No video to download, Inquire first')
            return

        if index is None:
            logger.info('Downloading all streams for video')
            yield from asyncio.wait(
                [self._download(video, i) for i in range(len(video.streams))])
        else:
            yield from self._download(video, index)
