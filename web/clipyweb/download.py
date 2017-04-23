"""
Clipy YouTube video downloader disk storage

DEBUG:asyncio:<_SelectorSocketTransport fd=9 read=polling write=<idle, bufsize=0>>: Fatal read error on socket transport
Traceback (most recent call last):
  File "/usr/lib/python3.6/asyncio/selector_events.py", line 724, in _read_ready
    data = self._sock.recv(self.max_size)
ConnectionResetError: [Errno 104] Connection reset by peer
"""
import os
import time
import asyncio
import logging

from aiohttp import ClientSession

# Limit number of downloads for calls to `get`
semaphore = asyncio.Semaphore(3)


async def get(stream, actives):
    """
    Govern downloading with a Semaphore
    """
    async with semaphore:
        return await _download(stream, actives)


async def _download(stream, actives):
    """
    Request stream's url and read from response and write to disk

    After every chunk is processed the stream's progress is updated.
    """
    async with ClientSession() as session:
        print(stream.url)
        async with session.get(stream.url) as response:

            total = int(response.headers.get('Content-Length', '0').strip())
            chunk_size = 16384
            bytesdone = 0
            offset = 0
            mode = "wb"
            t0 = time.time()
            temp_path = f'videos/{stream.path}.clipyweb'
            print(temp_path)

            # Taken from from Pafy https://github.com/np1/pafy
            if os.path.exists(temp_path):
                filesize = os.stat(temp_path).st_size

                if filesize < total:
                    mode = "ab"
                    bytesdone = offset = filesize
                    headers = dict(Range='bytes={}-'.format(offset))
                    response = await session.get(stream.url, headers=headers)

            complete = False

            with open(temp_path, mode) as fd:
                actives[stream.url] = stream

                while stream.url in actives:
                    chunk = await response.content.read(chunk_size)
                    print('chunk len:', len(chunk))
                    if len(chunk) == 0:
                        complete = True
                        break
                    fd.write(chunk)

                    bytesdone += len(chunk)

                    stream.progress.update(
                        bytesdone=bytesdone,
                        elapsed=time.time() - t0,
                        offset=offset,
                        total=total,
                    )
                    logging.info(stream.status)

                if stream.url in actives:
                    del actives[stream.url]

    if complete:
        os.rename(temp_path, f'videos/{stream.path}')

    return complete, bytesdone
