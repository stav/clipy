"""
Clipy YouTube video downloader network communications

g79HokJTfPU
gZAf4nJBpa0
mxvLMEyCXR0
"""
import aiohttp
import asyncio
import logging

import clipy.config

logger = logging.getLogger('clipy')


class Response(aiohttp.Response):
    """Manual response"""
    body = None

    def __init__(self, status):
        super(Response, self).__init__(None, status)

    @asyncio.coroutine
    def text(self):
        return self.body


@asyncio.coroutine
def _fetch_local(url, **kw):
    # Open connection to local server
    reader, writer = yield from asyncio.streams.open_connection('127.0.0.1', 8888)

    # Request the server for our url
    writer.write('{}\n'.format(url).encode("utf-8"))

    # Wait for the server response
    msgback = (yield from reader.readline()).decode("utf-8").rstrip()
    writer.close()

    if msgback.startswith('FAIL'):
        raise ConnectionError(msgback)

    # Build the client response
    response = Response(200)
    response.body = msgback

    return response


@asyncio.coroutine
def _fetch_network(url, **kw):
    try:
        response = yield from aiohttp.request('GET', url, **kw)

    except aiohttp.errors.OsConnectionError as ex:
        raise ConnectionError('Cannot connect') from ex

    # Debug
    # data = yield from response.text()
    # with open('fetch_network', 'w') as f:
    #     f.write('Url:       '); f.write(url);                   f.write('\n\n')
    #     f.write('Response:  '); f.write(str(response));         f.write('\n\n')
    #     f.write('Status:    '); f.write(str(response.status));  f.write('\n\n')
    #     f.write('Header:    '); f.write(str(response.headers)); f.write('\n\n')
    #     f.write('Data:      '); f.write(data);                  f.write('\n\n')

    return response


@asyncio.coroutine
def get(url, **kw):
    logger.debug('request get: {} {}'.format(url, kw if kw else ''))
    try:
        if clipy.config.LOCAL_NETWORK:
            response = yield from _fetch_local(url, **kw)
        else:
            response = yield from _fetch_network(url, **kw)

    except ConnectionError:
        raise

    if response.status < 200 or response.status > 299:
        raise ConnectionError('Bad response status: {}, {}'.format(response.status, url))

    return response


@asyncio.coroutine
def get_text(url):
    try:
        response = yield from get(url)

    except ConnectionError:
        raise

    data = yield from response.text()
    return data
