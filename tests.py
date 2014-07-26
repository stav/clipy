from __future__ import absolute_import, print_function, unicode_literals

import curses
import unittest
import pyperclip
import clipy.ui


class ClipyUITest(unittest.TestCase):

    console = None

    def setUp(self):
        def main(stdscr):
            self.console = clipy.ui.Window(stdscr, curses.LINES, curses.COLS, 0, 0)
            self.console.testing = True
        curses.wrapper(main)

    # def test_pafy_download_resume(self):
    #     """ Test resuming a partial download. """
    #     tempname = "WASTE  2 SECONDS OF YOUR LIFE-DsAn_n6O5Ns-171.ogg.temp"
    #     with open(tempname, "w") as ladeeda:
    #         ladeeda.write("abc")
    #     vid = pafy.new("DsAn_n6O5Ns", gdata=True)
    #     vstream = vid.audiostreams[-1].download(meta=True)
    #     name = "WASTE  2 SECONDS OF YOUR LIFE.ogg"
    #     self.assertEqual(22675, os.stat(name).st_size)

    def test_1_windows_created(self):
        """ Test that we can create the window abstration object correctly """
        self.assertIsInstance(self.console.box, type(curses.newwin(0, 0)))
        self.assertIsInstance(self.console.win, type(curses.newwin(0, 0)))

    def test_2_clipboard_communication(self):
        """ Test that we can read info from the clipboard """
        vid = 'mxvLMEyCXR0'
        pyperclip.copy(vid)
        self.assertEqual(vid, pyperclip.paste())

    def test_3_video_inquiry(self):
        """ Test that we can query YouTube and store info """
        vid = 'mxvLMEyCXR0'
        pyperclip.copy(vid)
        self.assertIsNone(self.console.video)
        clipy.ui.inquire(self.console)
        self.assertIsNotNone(self.console.video)

    # def test_4_download(self):
    #     """ Test that we can download from YouTube """
    # spawn(): need to remove vid selection logic


if __name__ == '__main__':
    # import pdb; pdb.set_trace()
    unittest.main(verbosity=2)
