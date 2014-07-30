import os


def download(stream, target='~', logger=print, callback=None):
    """ Download a video from YouTube. """
    target_dir = os.path.expanduser(target)

    def log(string, *a, **kw):
        if logger is print:
            logger(string)
        else:
            logger(string, *a, **kw)

    try:
        name = '{}-({}).{}'.format(stream.title, stream.quality, stream.extension)
        path = os.path.join(target_dir, name)
        # path = os.path.join(target_dir, stream.filename)
        log('Downloading {} `{}` to {}'.format(stream, stream.title, target_dir))
        if callback:
            filename = stream.download(filepath=path, quiet=True, callback=callback)
        else:
            filename = stream.download(filepath=path, quiet=False)

    except (OSError, ValueError, FileNotFoundError) as e:
        log(e, error=True)

    else:
        if log is print:
            log()
        if str(filename).endswith('.temp'):
            log('Partial download: `{}` ({})'.format(filename, stream))
        else:
            log('Downloaded: `{}` ({})'.format(filename, stream), success=True)
