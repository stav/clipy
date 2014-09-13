"""
Clipy YouTube video downloader test suite
"""
import curses
import asyncio
import unittest

import pyperclip

import clipy.panel
import clipy.window


class ClipyUITest(unittest.TestCase):

    def setUp(self):
        def main(stdscr):
            self.stdscr = stdscr
            win1 = clipy.window.DetailWindow(6, 10, 0, 0)
            win2 = clipy.window.ListWindow(6, 10, 10, 0)
            win3 = clipy.window.Window(6, 50, 20, 0)
            win4 = clipy.window.PopupWindow(3, 10, 10, 10)
            panl = clipy.panel.Panel(None, self.stdscr, win1, win2, win3, win4)
            panl.testing = True
            self.panel = panl
        curses.wrapper(main)

    def test_1_windows_created(self):
        """ Test that we can create the window abstration object correctly """
        win = clipy.window.Window(10, curses.COLS, 12, 0)
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


class ClipyAsyncTest(unittest.TestCase):

    def setUp(self):
        asyncio.get_event_loop().set_debug(True)

    def test_1_debug(self):
        self.assertIs(asyncio.get_event_loop().get_debug(), True)

    def test_2_call_soon(self):
        def normal_function():
            pass

        loop = asyncio.get_event_loop()
        loop.call_soon(normal_function())

    def test_3_coroutines(self):
        @asyncio.coroutine
        def coroutine_function_1():
            result = yield from coroutine_function_2()
            self.assertIs(result, True)

        @asyncio.coroutine
        def coroutine_function_2():
            return True

        loop = asyncio.get_event_loop()
        loop.run_until_complete(coroutine_function_1())

        # future = asyncio.Future()
        # loop.create_task(print_and_repeat(future))


if __name__ == '__main__':
    # import pdb; pdb.set_trace()
    unittest.main()
