import urllib

from aiohttp import ClientSession

from clipyweb.utils import get_video_id, take_first
from clipyweb.models import VideoDetail


# async def get(url):
#     async with ClientSession() as session:
#         async with session.get(url) as response:
#             return response


async def get_text(url, headers=None):
    async with ClientSession() as session:
        async with session.get(url) as response:
            body = await response.read()
            return body.decode('utf-8')


async def get_info(resource):
    url = f'https://www.youtube.com/get_video_info?video_id={resource}'
    data = await get_text(url)
    # print(f'get_info: data "{data}"')
    info = urllib.parse.parse_qs(data)
    status = take_first(info.get('status', None))
    if status == 'ok':
        return info
    else:
        raise ValueError('Invalid video Id "{}" {}'.format(resource, info))


async def get_video(url):
    vid = get_video_id(url)
    print(f'info: url "{url}", vid "{vid}"')
    data = await get_info(vid)
    # print(f'info: data "{data}"')

    video = VideoDetail(data)
    video.vid = vid

    return video
