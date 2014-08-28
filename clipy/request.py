"""
Clipy YouTube video downloader network communications

g79HokJTfPU
g79HokJTfP!
g79HokJTfP
"""
import os
import time
import aiohttp
import asyncio


# Limit number of downloads for calls to `governed_download`
semaphore = asyncio.Semaphore(3)


@asyncio.coroutine
def governed_download(stream, actives=None):
    """
    Request stream's url and read from response and write to disk obeying the
    law of Semaphores
    """
    with (yield from semaphore):
        response = yield from download(stream, actives)
        return response


@asyncio.coroutine
def download(stream, actives=None):
    """ Request stream's url and read from response and write to disk """
    response = yield from aiohttp.request('GET', stream.url)

    total = int(response.headers.get('Content-Length', '0').strip())
    chunk_size = 16384
    bytesdone = 0
    offset = 0
    mode = "wb"
    t0 = time.time()

    temp_path = stream.path + ".clipy"

    # Taken from from Pafy https://github.com/np1/pafy
    if os.path.exists(temp_path):
        filesize = os.stat(temp_path).st_size

        if filesize < total:
            mode = "ab"
            bytesdone = offset = filesize
            headers = dict(Range='bytes={}-'.format(offset))
            try:
                response = yield from aiohttp.request('GET', stream.url,
                                                      headers=headers)
            except aiohttp.errors.OsConnectionError as ex:
                raise ConnectionError from ex

    complete = False

    with open(temp_path, mode) as fd:

        while actives is None or stream.url in actives:
            chunk = yield from response.content.read(chunk_size)
            if not chunk:
                complete = True
                break
            fd.write(chunk)

            elapsed = time.time() - t0
            bytesdone += len(chunk)
            rate = ((bytesdone - offset) / 1024) / elapsed
            eta = (total - bytesdone) / (rate * 1024)
            progress_stats = (bytesdone, bytesdone * 1.0 / total, rate, eta)

            stream.status = '({total}) {:,} Bytes ({:.0%}) @ {:.0f} KB/s, ETA: {:.0f} secs  '.format(*progress_stats, total=total)

    if complete:
        os.rename(temp_path, stream.path)

    return complete, bytesdone


@asyncio.coroutine
def fetch(url, **kw):
    try:
        response = yield from aiohttp.request('GET', url, **kw)

    except aiohttp.errors.OsConnectionError as ex:
        raise ConnectionError from ex

    # Debug
    # data = yield from response.text()
    # with open('fetch', 'w') as f:
    #     f.write('Url:       '); f.write(url);                   f.write('\n\n')
    #     f.write('Response:  '); f.write(str(response));         f.write('\n\n')
    #     f.write('Status:    '); f.write(str(response.status));  f.write('\n\n')
    #     f.write('Header:    '); f.write(str(response.headers)); f.write('\n\n')
    #     f.write('Data:      '); f.write(data);                  f.write('\n\n')

    return response


@asyncio.coroutine
def get(url):
    try:
        response = yield from fetch(url)

    except ConnectionError as ex:
        raise ConnectionError from ex

    if response.status < 200 or response.status > 299:
        raise ConnectionError('Bad response status: {}, {}'.format(response.status, url))

    return response


@asyncio.coroutine
def get_text(url):
    try:
        response = yield from get(url)

    except ConnectionError as ex:
        raise ConnectionError from ex

    data = yield from response.text()
    return data
