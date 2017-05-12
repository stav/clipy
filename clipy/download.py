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

import aiohttp

logger = logging.getLogger(__name__)
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
    async with aiohttp.ClientSession() as session:
        async with session.get(stream.url) as response:

            total = int(response.headers.get('Content-Length', '0').strip())
            chunk_size = 2**14
            bytesdone = 0
            offset = 0
            mode = "wb"
            t0 = time.time()

            target_dir = 'videos'
            os.makedirs(target_dir, exist_ok=True)
            target_path = os.path.join(target_dir, stream.filename)
            temp_path = f'{target_path}.clipy'
            logger.info(f'{stream.sid} -> {temp_path}')

            # Taken from from Pafy https://github.com/np1/pafy
            if os.path.exists(temp_path):
                filesize = os.stat(temp_path).st_size

                if filesize < total:
                    mode = "ab"
                    bytesdone = offset = filesize
                    headers = dict(Range='bytes={}-'.format(offset))
                    logger.info(f'{stream.sid} exists, sending headers: {headers}')
                    response = await session.get(stream.url, headers=headers)

            complete = False

            with open(temp_path, mode) as fd:
                actives[stream.sid] = stream

                while stream.sid in actives:
                    chunk = await response.content.read(chunk_size)
                    # length = len(chunk)
                    # logger.debug(f'@@@ {stream.sid} chunk len {length}')
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

                active = stream.sid in actives
                logger.debug(f'{stream.sid} finished, active? {active}')
                if stream.sid in actives:
                    del actives[stream.sid]

    if complete:
        os.rename(temp_path, target_path)

    return complete, bytesdone
