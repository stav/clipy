"""
Clipy

Command Line Interface using Python for Youtube

Python commmand-line YouTube video downloader.
"""
import os
import sys
import asyncio
import argparse

# import pyperclip - lazy import
# import clipy.download - lazy import
# import clipy.ui - lazy import
# import clipy.youtube - lazy import

VERSION = '0.9.7'


def _get_commandline_options():
    """
    Parse command line.
    """
    # declare command-line argument parser
    command_line = argparse.ArgumentParser(
        description='YouTube video downloader',
        epilog='E.g.: clipy http://www.youtube.com/watch?v=fm78gjYkYKc -d',
        )

    # define the command-line arguments
    command_line.add_argument(
        'resource', metavar='RESOURCE', type=str, nargs='?',
        help='URL or video Id')

    command_line.add_argument(
        '-d', '--download', type=int, nargs='?', default=None, const=0,
        help='Downloaded a stream, default 0')

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
    resource = options.resource
    target_dir = os.path.expanduser(options.target)

    log('Clipy started with {}'.format(options))

    import clipy.youtube

    if options.clipboard:
        if options.resource:
            log('WARNING: attempting to override supplied resource "{}" with'
                ' clipboard contents'.format(options.resource))
        log('Checking clipboard for resource')
        import pyperclip
        resource = pyperclip.paste().strip()

    if not resource:
        print('No resource supplied')
        return

    log('Using resource: {}'.format(resource))
    try:
        video = yield from clipy.youtube.get_video(resource, target=target_dir)
    except (ConnectionError, ValueError) as ex:
        print(ex)

    if video:
        log('Video found on YouTube')
        print(video.detail)

        if options.download is not None:
            print('Stream selected: {}'.format(options.download))
            try:
                stream = video.streams[options.download]
            except IndexError:
                print('Stream {} not found, available streams are {}'.format(
                    options.download, [i for i in range(len(video.streams))]))

            if stream:
                print(stream.detail())
                print('Downloading to {}'.format(stream.path))

                import clipy.download
                _success, _length = yield from clipy.download.get(
                    stream, log=sys.stdout)

                print('\nDownload of {} bytes {}'.format(_length,
                      'completed normally' if _success else 'did not complete'))

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
