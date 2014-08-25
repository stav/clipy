"""
Clipy YouTube video downloader network communications

g79HokJTfPU
g79HokJTfP!
g79HokJTfP
"""
from __future__ import absolute_import, division, print_function, unicode_literals

import time
import aiohttp
import asyncio


@asyncio.coroutine
def download(url,
             port=80, path='~', active_poll=lambda: True,
             progress_callback=lambda *a: None):

    bytesdone = 0
    chunk_size = 16384
    t0 = time.time()

    response = yield from aiohttp.request('GET', url)
    total = int(response.headers.get('Content-Length', 0).strip())
    complete = False

    with open(path, 'wb') as fd:
        while active_poll():
            chunk = yield from response.content.read(chunk_size)
            if not chunk:
                complete = True
                break
            fd.write(chunk)

            elapsed = time.time() - t0
            bytesdone += len(chunk)
            rate = (bytesdone / 1024) / elapsed
            eta = (total - bytesdone) / (rate * 1024)
            progress_stats = (bytesdone, bytesdone * 1.0 / total, rate, eta)
            progress_callback(url, total, *progress_stats)

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
    response = yield from fetch(url)

    if response.status < 200 or response.status > 299:
        raise ConnectionError('Bad response status: {}, {}'.format(response.status, url))

    return response


@asyncio.coroutine
def get_text(url):
    try:
        response = yield from get(url)
    except:
        raise

    data = yield from response.text()
    return data
