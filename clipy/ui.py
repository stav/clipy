"""
Clipy YouTube video downloader user interface
"""
import os
import curses
import asyncio

import clipy.panel
import clipy.window

TITLE = '.:. Clipy .:.'
VERSION = '0.9.33'

loop = None


def async(task):
    loop.call_soon_threadsafe(asyncio.async, task)


def key_loop(stdscr, panel):
    KEYS_DOWNLOAD = (ord('d'),)
    KEYS_DOWNLALL = (ord('D'),)
    KEYS_INPUT    = (ord('i'), ord('I'))
    KEYS_CLIPBOARD= (ord('c'), ord('C'))
    KEYS_HELP     = (ord('h'), ord('H'))
    KEYS_QUIT     = (ord('q'), ord('Q'))
    KEYS_RESET    = (ord('R'),)
    KEYS_CACHE    = (ord('L'), ord('S'), curses.KEY_LEFT, curses.KEY_RIGHT,
                     curses.KEY_UP, curses.KEY_DOWN)
    KEYS_ACTION   = (curses.KEY_ENTER, 10)  # 10 is enter

    while True:

        # Refresh screen with each keystroke for snappy display
        stdscr.noutrefresh()
        panel.display()

        # Accept keyboard input
        c = panel.wait_for_input()

        if c in KEYS_QUIT:      break
        if c in KEYS_INPUT:     async(panel.inquire(panel.popup.get_input()))
        if c in KEYS_ACTION:    async(panel.action())
        if c in KEYS_CLIPBOARD: async(panel.clipboard())
        if c in KEYS_DOWNLOAD:  async(panel.download(panel.detail.video, 0))
        if c in KEYS_DOWNLALL:  async(panel.download(panel.detail.video))
        if c in KEYS_CACHE:           panel.view(c)
        if c in KEYS_RESET:           panel.reset()
        if c in (ord('Z'),):    async(panel.inquire('g79HokJTfPU'))  # Debug

        if c in KEYS_HELP:
            panel.console.printstr(
                'HELP: Load cache (L), save cache (S), reset (R) and download all (D)'
                ' commands are all upper case only.', wow=True)

        # Show last key pressed
        stdscr.addstr(curses.LINES-1, curses.COLS-20, 'c={}'.format(c))


def init(stdscr, resource, target):

    # Setup curses
    curses.curs_set(False)
    curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(3, curses.COLOR_BLACK, curses.COLOR_YELLOW)
    if curses.has_colors():
        curses.start_color()

    # Title bar at top
    stdscr.addstr(TITLE, curses.A_REVERSE)
    stdscr.chgat(-1, curses.A_REVERSE)
    version = 'UIv {} '.format(VERSION)
    stdscr.addstr(0, curses.COLS-len(version), version, curses.A_REVERSE)

    # Menu options at bottom
    menu_options = (
        ('I', 'input'),
        ('C', 'clipboard'),
        ('arrows', 'cache'),
        ('L', 'load cache'),
        ('S', 'save cache'),
        ('d', 'download one'),
        ('D', 'download all'),
        ('R', 'reset'),
        ('H', 'help'),
        ('Q', 'quit'),
    )
    menu_string = 'Press: ' + ', '.join(
        ['{}: {}'.format(k, v) for k, v in menu_options])
    stdscr.addstr(curses.LINES-1, 0, menu_string)

    # Create the middle three windows and the popoup
    L = curses.LINES
    C = curses.COLS
    detail  = clipy.window.DetailWindow(  L-9,   C//2,    1  ,    0        )
    cache   = clipy.window.ListWindow  (  L-9,   C//2,    1  ,   C - C//2  )
    console = clipy.window.Window      (   7 ,   C   ,   L-8 ,    0        )
    popup   = clipy.window.PopupWindow (   3 ,   C//2,   L//4,   C//4      )

    # Create control panel
    control_panel = clipy.panel.Panel(loop, stdscr, detail, cache, console, popup)

    # Load command line options
    control_panel.target_dir = os.path.expanduser(target)
    control_panel.reset()  # lame binding for target_dir
    if resource:
        stdscr.noutrefresh()
        async(control_panel.inquire(resource))

    def status_poll():
        """ Refresh screen 10x/s when downloads active """
        loop.call_later(0.1, status_poll)

        if control_panel.cache.actives:
            stdscr.noutrefresh()
            control_panel.display()

    loop.call_soon_threadsafe(status_poll)

    # Enter curses keyboard event loop
    key_loop(stdscr, control_panel)

    # After the curses loop has finished we then stop the Python loop
    loop.call_soon_threadsafe(loop.stop)


def main(resource=None, target=None):
    """
    Single entry point to run two event loops:

    1. Python `asyncio` event loop
    2. Curses wrapper runs init in another thread which in-turn runs `key_loop`
    """
    global loop
    # Python event loop
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_in_executor(None, curses.wrapper, *(init, resource, target))
    loop.run_forever()
    loop.close()


if __name__ == '__main__':
    main()
