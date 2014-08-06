from __future__ import absolute_import, print_function, unicode_literals

import curses
import unittest
import pyperclip
import clipy.ui


class ClipyUITest(unittest.TestCase):

    def setUp(self):
        def main(stdscr):
            self.stdscr = stdscr
            win1 = clipy.ui.DetailWindow(6, 10, 0, 0)
            win2 = clipy.ui.ListWindow(6, 10, 10, 0)
            win3 = clipy.ui.Window(6, 10, 20, 0)
            panl = clipy.ui.Panel(self.stdscr, win1, win2, win3)
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
        pyperclip.copy( vid )
        self.assertEqual( vid, pyperclip.paste() )

    def test_3_reset(self):
        """ Test that we can reset """
        self.assertIsNone(self.panel.detail.video)
        self.panel.detail.video = object()
        self.assertIsNotNone(self.panel.detail.video)
        self.panel.reset()
        self.assertIsNone(self.panel.detail.video)


if __name__ == '__main__':
    # import pdb; pdb.set_trace()
    unittest.main(verbosity=2)
