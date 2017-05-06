import logging
import urllib

import aiohttp

import clipy.utils
import clipy.models

from clipy.utils import take_first as tf

logger = logging.getLogger(__name__)


async def get_text(url, headers=None):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            body = await response.read()
            return body.decode('utf-8')


async def get_info(vid):
    url = f'https://www.youtube.com/get_video_info?video_id={vid}'
    data = await get_text(url)
    info = urllib.parse.parse_qs(data)
    status = tf(info.get('status', None))
    if status == 'ok':
        return info
    else:
        raise ValueError('Invalid video Id "{}" {}'.format(vid, info))


async def get_video(url):
    vid = clipy.utils.get_video_id(url)
    logger.debug(f'url "{url}" --> vid "{vid}"')
    data = await get_info(vid)
    video = clipy.models.VideoModel(vid, data)

    return video


async def get_stream(sid):
    vid, _, idx = sid.partition('|')
    logger.debug(f'sid "{sid}" --> ({vid}, {idx})')
    data = await get_info(vid)
    video = clipy.models.VideoModel(vid, data, index=idx)

    return video.stream
