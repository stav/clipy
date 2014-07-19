import os
import signal
import asyncio
import functools

import pafy
import pyperclip


def download(video):
    download_dir = os.path.expanduser('~')
    try:
        best = video.getbest(preftype="mp4")
        print('engaged:', '\n%s\n%s' % (video.title, best))
        path = '%s.%s' % (os.path.join(download_dir, best.title), best.extension)
        best.download(filepath=path)
    except (OSError, ValueError, FileNotFoundError) as e:
        print(e)


def ask_exit(loop):
    url = pyperclip.paste().strip()

    print('\nChecking clipboard: "%s"' % url)
    cmds = dict(x=lambda: loop.stop())

    try:
        video = pafy.new(url)
        print(video)
        cmds['d'] = functools.partial(download, video)
    except ValueError as e:
        print(e)

    cmd = input('Enter a command: %s or just <Enter> to continue:\n' %
        [c for c in cmds.keys()])

    if cmd in cmds:
        cmds[cmd]()

def main():
    loop = asyncio.get_event_loop()

    loop.add_signal_handler(signal.SIGINT, functools.partial(ask_exit, loop))

    print("Event loop running (pid %s), press CTRL+c to interrupt." % os.getpid())

    try:
        loop.run_forever()
    finally:
        loop.close()

if __name__ == '__main__':
    main()
