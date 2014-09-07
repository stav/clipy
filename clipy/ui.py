"""
Clipy YouTube video downloader user interface
"""
import os
import curses
import asyncio

import clipy.panel
import clipy.window

TITLE = '.:. Clipy .:.'
VERSION = '0.9.27'


def key_loop(stdscr, panel):
    KEYS_DOWNLOAD = (ord('d'), ord('D'))
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

        # Allow cache keys during input mode
        if c in KEYS_CACHE:
            panel.view(c)

        # Allow action keys during input mode
        elif c in KEYS_ACTION:
            panel.loop.call_soon_threadsafe(asyncio.async, panel.action())

        # Check for input mode
        elif panel.input_mode:
            if c == 27:  # escape
                panel.input_mode = False
            else:
                panel.input_text += chr(c)

        # The following keys are not captured during input mode
        else:

            if c in KEYS_QUIT:
                break

            if c in KEYS_RESET:
                panel.reset()

            if c in KEYS_INPUT:
                # panel.loop.call_soon_threadsafe(asyncio.async, panel.input())
                panel.input_mode = True
                panel.input_text = ''
                # curses.nocbreak()
                # self.stdscr.keypad(False)
                # curses.echo()

            if c in KEYS_CLIPBOARD:
                panel.loop.call_soon_threadsafe(asyncio.async, panel.clipboard())

            if c in KEYS_DOWNLOAD:
                panel.loop.call_soon_threadsafe(asyncio.async, panel.download(
                    panel.detail.video))

            if c in KEYS_HELP:
                panel.console.printstr(
                    'HELP: Load cache (L), save cache (C) and reset (R)'
                    ' commands are all upper case only.', wow=True)

            # Debug
            if c in (ord('Z'),):
                panel.loop.call_soon_threadsafe(
                    asyncio.async, panel.inquire('g79HokJTfPU'))

        # Show last key pressed
        stdscr.addstr(curses.LINES-1, curses.COLS-20, 'c={}'.format(c))


def init(stdscr, loop, resource, target):

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
        ('I', 'input'),
        ('C', 'clipboard'),
        ('arrows', 'cache'),
        ('L', 'load cache'),
        ('S', 'save cache'),
        ('D', 'download'),
        ('R', 'reset'),
        ('H', 'help'),
        ('Q', 'quit'),
    )
    menu_string = 'Press: ' + ', '.join(
        ['{}: {}'.format(k, v) for k, v in menu_options])
    stdscr.addstr(curses.LINES-1, 0, menu_string)

    # Create the middle three windows
    detail  = clipy.window.DetailWindow(curses.LINES-9, curses.COLS//2,              1, 0                           )
    cache   = clipy.window.ListWindow  (curses.LINES-9, curses.COLS//2,              1, curses.COLS - curses.COLS//2)
    console = clipy.window.Window      (7             , curses.COLS   , curses.LINES-8, 0                           )
    control_panel = clipy.panel.Panel(loop, stdscr, detail, cache, console)

    # Load command line options
    control_panel.target_dir = os.path.expanduser(target)
    if resource:
        stdscr.noutrefresh()
        loop.call_soon_threadsafe(asyncio.async, control_panel.inquire(resource))

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
    # Python event loop
    loop = asyncio.get_event_loop()
    loop.set_debug(True)
    loop.run_in_executor(None, curses.wrapper, *(init, loop, resource, target))
    loop.run_forever()
    loop.close()


if __name__ == '__main__':
    main()
