from __future__ import absolute_import, division, print_function, unicode_literals

import os
import time
import aiohttp
import asyncio
import urllib


@asyncio.coroutine
def download(url,
             port=80, filename='~', active_poll=lambda: True,
             progress_callback=lambda *a: None):

    bytesdone = 0
    chunk_size = 16384
    t0 = time.time()

    response = yield from aiohttp.request('GET', url)
    total = int(response.headers.get('Content-Length', 0).strip())

    with open(filename, 'wb') as fd:
        while active_poll():
            chunk = yield from response.content.read(chunk_size)
            if not chunk:
                break
            fd.write(chunk)

            elapsed = time.time() - t0
            bytesdone += len(chunk)
            rate = (bytesdone / 1024) / elapsed
            eta = (total - bytesdone) / (rate * 1024)
            progress_stats = (bytesdone, bytesdone * 1.0 / total, rate, eta)
            progress_callback(total, *progress_stats)

    return bytesdone


@asyncio.coroutine
def fetch(url, port=80, logger=print):

    def _log(string, *a, **kw):
        if logger is print:
            logger(string)
        else:
            logger(string, *a, **kw)

    _log('* url: ({}) {}'.format(len(url), url))

    host = urllib.parse.urlparse(url).hostname

    # opener = build_opener()
    # response = opener.open(url)
    # total = int(response.info()['Content-Length'].strip())
    # _log('* total: {}'.format(total))

    r, w = yield from asyncio.open_connection(host, port)
    request = '''GET {url} HTTP/1.1
Host: {host}
User-Agent: Python asyncio clipy

'''.format(url=url, host=host)
    _log('> request: {}'.format(request))

    w.write(request.encode('latin-1'))

    while True:
        line = yield from r.readline()
        line = line.decode('latin-1').rstrip()
        if not line:
            break
        _log('< {}'.format(line))

    # print(file=sys.stderr)
    body = yield from r.read()

    return body


def download_pafy(stream, target='~', logger=print,
                  progress_callback=None, done_callback=lambda *a: None):
    """ Download a video from YouTube. """
    target_dir = os.path.expanduser(target)
    success = False
    filename = ''

    def log(string, *a, **kw):
        if logger is print:
            logger(string)
        else:
            logger(string, *a, **kw)

    try:
        name = '{}-({}).{}'.format(
            stream.title, stream.quality, stream.extension).replace('/', '|')
        path = os.path.join(target_dir, name)
        log('Downloading {} `{}` to {}'.format(
            stream, stream.title, target_dir))
        if progress_callback:
            cb = progress_callback
            filename = stream.download(filepath=path, quiet=True, callback=cb)
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
            success = True

    finally:
        done_callback(stream, filename, success)
