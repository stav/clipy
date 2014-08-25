from __future__ import absolute_import, print_function, unicode_literals

import curses
import asyncio
import unittest
import pyperclip
import clipy.ui


class ClipyUITest(unittest.TestCase):

    def setUp(self):
        def main(stdscr):
            self.stdscr = stdscr
            win1 = clipy.ui.DetailWindow(6, 10, 0, 0)
            win2 = clipy.ui.ListWindow(6, 10, 10, 0)
            win3 = clipy.ui.Window(6, 50, 20, 0)
            panl = clipy.ui.Panel(self.stdscr, win1, win2, win3)
            panl.testing = True
            self.panel = panl
        curses.wrapper(main)

    def test_1_windows_created(self):
        """ Test that we can create the window abstration object correctly """
        win = clipy.ui.Window(10, curses.COLS, 12, 0)
        self.assertIsInstance(win.box, type(curses.newwin(0, 0)))
        self.assertIsInstance(win.win, type(curses.newwin(0, 0)))

    def test_2_clipboard_communication(self):
        """ Test that we can read info from the clipboard """
        vid = 'mxvLMEyCXR0'
        pyperclip.copy(vid)
        self.assertEqual(vid, pyperclip.paste())

    def test_3_reset(self):
        """ Test that we can reset """
        self.assertIsNone(self.panel.detail.video)
        self.assertIsNotNone(self.panel.cache.videos)
        self.panel.detail.video = object()
        self.panel.cache.videos = None
        self.assertIsNotNone(self.panel.detail.video)
        self.assertIsNone(self.panel.cache.videos)
        self.panel.reset()
        self.assertIsNone(self.panel.detail.video)
        self.assertIsNotNone(self.panel.cache.videos)

    def test_4_streams(self):
        """ Test that we can toggle streams display flag """
        self.assertIs(self.panel.detail.streams, False)
        self.panel.streams()
        self.assertIs(self.panel.detail.streams, True)


class ClipyAsyncTest(unittest.TestCase):

    def setUp(self):
        asyncio.get_event_loop().set_debug(True)

    def test_primera(self):
        self.assertIs(asyncio.get_event_loop().get_debug(), True)

    def test_coroutine(self):
        @asyncio.coroutine
        def print_and_repeat():
            return 'asdf'

        loop = asyncio.get_event_loop()
        result = yield from print_and_repeat()
        # loop.call_soon(print_and_repeat)
        asdf

        # # future = asyncio.Future()
        # # loop.create_task(print_and_repeat(future))

        # try:
        #     loop.run_until_complete(print_and_repeat())
        # finally:
        #     loop.close()

        # self.assertEqual(result, 'qwer')


if __name__ == '__main__':
    # import pdb; pdb.set_trace()
    unittest.main(verbosity=2)
