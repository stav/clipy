"""
Clipy YouTube video downloader disk storage
"""
import os
import time
import asyncio

from aiohttp import ClientSession

import clipyweb
import clipyweb.utils

# Limit number of downloads for calls to `get`
semaphore = asyncio.Semaphore(3)


@asyncio.coroutine
def get(stream, actives=None, log=None):
    """
    Govern downloading with a Semaphore
    """
    try:
        with (yield from semaphore):
            response = yield from _download(stream, actives, log)
            return response

    except ConnectionError:
        raise


async def _download(stream, actives, log):
    """
    Request stream's url and read from response and write to disk

    After every chunk is processed the stream's status is updated.
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

            temp_path = stream.path + ".clipyweb"
            print(temp_path)

            complete = False

            with open(temp_path, mode) as fd:
                while True:
                    chunk = await response.content.read(chunk_size)
                    if not chunk:
                        complete = True
                        break
                    fd.write(chunk)

                    elapsed = time.time() - t0
                    bytesdone += len(chunk)
                    rate = ((bytesdone - offset) / 1024) / elapsed
                    eta = (total - bytesdone) / (rate * 1024)

                    stream.status = '|{m}| {d:,} ({p:.0%}) {t} @ {r:.0f} KB/s {e:.0f} s'.format(
                        m=clipyweb.utils.progress_bar(bytesdone, total),
                        d=bytesdone,
                        t=clipyweb.utils.size(total),
                        p=bytesdone * 1.0 / total,
                        r=rate,
                        e=eta,
                    )
                    if log:
                        log.write("\r{}    ".format(stream.status))
                        # log.flush()

    if complete:
        os.rename(temp_path, stream.path)

    return complete, bytesdone
