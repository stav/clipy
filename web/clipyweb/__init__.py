import urllib

from aiohttp import ClientSession

from clipyweb.utils import get_video_id, take_first
from clipyweb.models import VideoDetail


async def get(url):
    async with ClientSession() as session:
        async with session.get(url) as response:
            body = await response.read()
            return body.decode('utf-8')


async def get_info(resource):
    url = 'https://www.youtube.com/get_video_info?video_id={}'.format(resource)
    data = await get(url)
    # print(f'get_info: data "{data}"')
    info = urllib.parse.parse_qs(data)
    status = take_first(info.get('status', None))
    if status == 'ok':
        return data
    else:
        raise ValueError('Invalid video Id "{}" {}'.format(resource, info))


async def info(url):
    vid = get_video_id(url)
    print(f'info: url "{url}", vid "{vid}"')
    data = await get_info(vid)
    print(f'info: data "{data}"')
    return VideoDetail(data)
