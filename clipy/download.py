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

logger = logging.getLogger('clipy:downloader')
semaphore = asyncio.Semaphore(3)  # Limit number of downloads for calls to ``get``


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
        logger.debug(stream.hash)
        async with session.get(stream.url) as response:

            total = int(response.headers.get('Content-Length', '0').strip())
            chunk_size = 16384
            bytesdone = 0
            offset = 0
            mode = "wb"
            t0 = time.time()

            target_dir = 'videos'
            os.makedirs(target_dir, exist_ok=True)
            target_path = os.path.join(target_dir, stream.name)
            temp_path = f'{target_path}.clipy'
            logger.debug(temp_path)

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
                actives[stream.hash] = stream

                while stream.hash in actives:
                    chunk = await response.content.read(chunk_size)
                    logger.debug('chunk len: {}'.format(len(chunk)))
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
                    logger.info(stream.status)

                if stream.hash in actives:
                    del actives[stream.hash]

    if complete:
        os.rename(temp_path, target_path)

    return complete, bytesdone
