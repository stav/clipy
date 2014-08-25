"""
Clipy

Command Line Interface using Python for Youtube

Python commmand-line YouTube video downloader.
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import os
import sys
import asyncio
import argparse

# import pyperclip - lazy import
# import clipy.request - lazy import
# import clipy.ui - lazy import
# import clipy.youtube - lazy import

VERSION = '0.9.3'


def _get_commandline_options():
    """
    Parse command line.
    """
    # declare command-line argument parser
    command_line = argparse.ArgumentParser(
        description='YouTube video downloader',
        epilog='E.g.: clipy http://www.youtube.com/watch?v=fm78gjYkYKc -d -s1',
        )

    # define the command-line arguments
    command_line.add_argument(
        'resource', metavar='RESOURCE', type=str, nargs='?',
        help='URL or video Id')

    command_line.add_argument(
        '-d', '--download', action='store_true',
        help='Downloaded a stream')

    command_line.add_argument(
        '-s', '--stream', metavar='S', type=int,
        help='Select stream to download: 0, 1, 2, 3...')

    command_line.add_argument(
        '-t', '--target', metavar='DIR', type=str,
        help='Target folder to save to', default='~')

    command_line.add_argument(
        '-c', '--clipboard', action='store_true',
        help='Check clipboard for resource')

    command_line.add_argument(
        '-u', '--ui', action='store_true',
        help='Start the user interface menu')

    command_line.add_argument(
        '-l', dest='logger', metavar='LOGFILE',
        nargs='?', default=lambda *a: None, const=print,
        help='Logging enabled, option must follow RESOURCE')

    # command_line.add_argument('-o', dest='outputfile', metavar='OUFL', nargs='?',
    # type=argparse.FileType('w'), default=sys.stdout, const='/dev/null',
    # help='output filename, def=stdout, const=/dev/null')

    command_line.add_argument(
        '-V', '--version', action='version',
        version=VERSION,
        help='print the version information and exit')

    return command_line.parse_args(sys.argv[1:])


@asyncio.coroutine
def init(options):
    """ Non-user interface """
    log = options.logger
    video = None
    stream = None
    resource = None
    target_dir = os.path.expanduser(options.target)

    log('Clipy started with {}'.format(options))

    import clipy.youtube

    if options.resource:
        log('Supplied resource: {}'.format(options.resource))
        try:
            video = yield from clipy.youtube.get_video(
                options.resource, target=target_dir)

        except ConnectionError as ex:
            log('Error: Cannot connect {}'.format(ex))

    if video is None and options.clipboard:
        log('Checking clipboard for resource')
        import pyperclip
        resource = pyperclip.paste().strip()

        video = yield from clipy.youtube.get_video(
            resource, target=target_dir)

    if video:
        log('Video found on YouTube')
        print(video.detail)

        if options.stream is not None:
            log('Stream selected: {}'.format(options.stream))
            try:
                stream = video.streams[options.stream]
            except IndexError:
                print('Stream {} not found in {}'.format(
                    options.stream, video.streams))
            else:
                for p in dir(stream):
                    attr = getattr(stream, p, None)
                    if not p.startswith('_') and not hasattr(attr, '__call__'):
                        print('{}: {}'.format(p, getattr(stream, p, '')))

    if options.download:
        if video is None:
            print('No valid resource provided {} {}'.format(
                options.resource or '', resource or ''))
        elif stream is None:
            print('No stream selected for download')
        else:
            import clipy.request
            print('Downloading...')
            _success, _length = yield from clipy.request.download(stream)

    log('Clipy stopping')


def main():
    """ Script entry point """
    options = _get_commandline_options()

    if options.ui:
        import clipy.ui
        clipy.ui.main(options.resource, options.target)

    else:
        loop = asyncio.get_event_loop()
        loop.set_debug(True)
        loop.run_until_complete(init(options))
        loop.close()


if __name__ == '__main__':
    main()
