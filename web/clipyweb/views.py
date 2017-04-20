import json

import aiohttp
import aiohttp_jinja2

import clipyweb
import clipyweb.download


async def inquire(request):
    video_url = request.query.get('video')
    video = await clipyweb.get_video(video_url)
    data = dict(
        description=video.description,
        duration=video.duration,
        streams=[str(s) for s in video.streams],
        title=video.title,
        vid=video.vid,
    )
    return aiohttp.web.Response(
        content_type='application/json',
        text=json.dumps(data),
    )


async def download(request):
    vid = request.query.get('vid')
    index = int(request.query.get('index'))
    video = await clipyweb.get_video(vid)
    data = await clipyweb.download.get(video.streams[index])

    return aiohttp.web.Response(
        content_type='application/json',
        text=json.dumps(data),
    )


@aiohttp_jinja2.template('index.html')
async def index(request):
    return {
        'question': 'question',
        'choices': 'choices'
    }
