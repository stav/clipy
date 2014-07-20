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
        path = '%s.%s' % (os.path.join(download_dir, best.title), best.extension)
        print('Downloading', best, path)
        best.download(filepath=path)
    except (OSError, ValueError, FileNotFoundError) as e:
        print(e)


def inquire(loop):
    url = pyperclip.paste().strip()

    print()
    print('\nChecking clipboard: "%s"' % url)
    cmds = dict(x=lambda: loop.stop())

    try:
        video = pafy.new(url)
        print(video)
        print('allstreams', video.allstreams)
        cmds['d'] = functools.partial(download, video)
    except ValueError as e:
        print(e)

    cmd = input('> Enter a command: %s or just <Enter> to continue:\n' %
        [c for c in cmds.keys()])

    if cmd in cmds:
        cmds[cmd]()

def main():
    loop = asyncio.get_event_loop()

    loop.add_signal_handler(signal.SIGINT, functools.partial(inquire, loop))

    print()
    print("Event loop running (pid %s), press CTRL+c to interrupt." % os.getpid())

    try:
        loop.run_forever()
    finally:
        loop.close()

if __name__ == '__main__':
    main()
