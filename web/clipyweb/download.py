"""
Clipy YouTube video downloader disk storage
"""
import os
import time
import asyncio

from aiohttp import ClientSession

import clipyweb.utils

# Limit number of downloads for calls to `get`
semaphore = asyncio.Semaphore(3)


async def get(stream, actives, log=None):
    """
    Govern downloading with a Semaphore
    """
    with (await semaphore):
        return await _download(stream, actives, log)


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
            temp_path = f'videos/{stream.path}.clipyweb'
            print(temp_path)
            # Add back in offset download
            complete = False

            with open(temp_path, mode) as fd:
                while stream.url in actives:
                    index = actives.index(stream.url)
                    chunk = await response.content.read(chunk_size)
                    print('chunk len:', len(chunk))
                    if len(chunk) == 0:
                        complete = True
                        break
                    fd.write(chunk)

                    elapsed = time.time() - t0
                    bytesdone += len(chunk)
                    rate = ((bytesdone - offset) / 1024) / elapsed
                    eta = (total - bytesdone) / (rate * 1024)

                    stream.status = '{i}|{m}| {d:,} ({p:.0%}) {t} @ {r:.0f} KB/s {e:.0f} s'.format(
                        i=' ' * (index * 70),
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
        os.rename(temp_path, f'videos/{stream.path}')

    return complete, bytesdone
