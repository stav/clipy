"""
Clipy

Command Line Interface using Python for Youtube

Python commmand-line YouTube video downloader.

mxvLMEyCXR0
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import sys
import argparse

import pafy
# import pyperclip - lazy import
# import clipy.request - lazy import
# import clipy.ui - lazy import

VERSION = '0.8'


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
    command_line.add_argument('resource', metavar='RESOURCE', type=str, nargs='?',
                        help='URL or video Id')

    command_line.add_argument('-d', '--download', action='store_true',
                        help='Downloaded a stream')

    command_line.add_argument('-s', '--stream', metavar='S', type=int,
                        help='Select stream to download: 0, 1, 2, 3...')

    command_line.add_argument('-t', '--target', metavar='DIR', type=str,
                        help='Target folder to save to', default='~')

    command_line.add_argument('-c', '--clipboard', action='store_true',
                        help='Check clipboard for resource')

    command_line.add_argument('-u', '--ui', action='store_true',
                        help='Start the user interface menu')

    command_line.add_argument('-l', dest='logger', metavar='LOGFILE',
                        nargs='?', default=lambda *a: None, const=print,
                        help='Logging enabled, option must follow RESOURCE')

    # command_line.add_argument('-i', dest='inputfile', nargs='?', metavar='INFL',
    #                     type=argparse.FileType('rU'), default=sys.stdin,
    #                     help='input filename, def=stdin')

    # command_line.add_argument('-o', dest='outputfile', metavar='OUFL', nargs='?',
    #                     type=argparse.FileType('w'), default=sys.stdout, const='/dev/null',
    #                     help='output filename, def=stdout, const=/dev/null')

    command_line.add_argument('-V', '--version', action='version',
                        version=VERSION,
                        help='print the version information and exit')

    return command_line.parse_args(sys.argv[1:])


def _get_video(resource):
    """ Create new Pafy video instance """
    try:
        return pafy.new(resource)
    except (OSError, ValueError) as ex:
        print(ex)


def main():
    """ Script entry point """
    options = _get_commandline_options()
    log = options.logger
    video = None
    stream = None
    resource = None

    log('Clipy started with {}'.format(options))

    if options.resource:
        log('Supplied resource: {}'.format(options.resource))
        video = _get_video(options.resource)

    if video is None and options.clipboard:
        log('Checking clipboard for resource')
        import pyperclip
        resource = pyperclip.paste().strip()
        video = _get_video(resource)

    if video:
        log('Video found on YouTube ')
        print(video)
        for i, stm in enumerate(video.allstreams):
            print('{}: {} {} {} {} {}'.format(i,
                stm.mediatype,
                stm.quality,
                stm.extension,
                stm.notes,
                stm.bitrate or ''))
        if options.stream is not None:
            log('Stream selected: {}'.format(options.stream))
            try:
                stream = video.allstreams[options.stream]
            except IndexError:
                print('Stream {} not found in {}'.format(
                    options.stream, video.allstreams))
            else:
                for prop in dir(stream):
                    attr = getattr(stream, prop, None)
                    if not prop.startswith('_') and not hasattr(attr, '__call__'):
                        print('{}: {}'.format(prop, getattr(stream, prop, '')))

    if options.ui:
        try:
            import clipy.ui
            clipy.ui.main(video, stream, options.target)
        except ImportError:
            from ui import main
            main(video, stream, options.target)

    elif options.download:
        if video is None:
            print('No valid resource provided {} {}'.format(
                options.resource or '', resource or ''))
        elif stream is None:
            print('No stream selected for download')
        else:
            try:
                import clipy.request
                clipy.request.download(stream, options.target)
            except ImportError:
                from request import download
                download(stream, options.target)

    log('Clipy stopping')


if __name__ == '__main__':
    main()