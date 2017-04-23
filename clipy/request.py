import urllib

import aiohttp

import clipy.utils
import clipy.models

from clipy.utils import take_first as tf


async def get_text(url, headers=None):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            body = await response.read()
            return body.decode('utf-8')


async def get_info(resource):
    url = f'https://www.youtube.com/get_video_info?video_id={resource}'
    data = await get_text(url)
    # print(f'get_info: data "{data}"')
    info = urllib.parse.parse_qs(data)
    status = tf(info.get('status', None))
    if status == 'ok':
        return info
    else:
        raise ValueError('Invalid video Id "{}" {}'.format(resource, info))


async def get_video(url):
    vid = clipy.utils.get_video_id(url)
    print(f'info: url "{url}", vid "{vid}"')
    data = await get_info(vid)
    video = clipy.models.VideoDetail(vid, data)

    return video
