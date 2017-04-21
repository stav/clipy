import sys
import json

import aiohttp
import aiohttp_jinja2

import clipyweb.request
import clipyweb.download


async def inquire(request):
    video_url = request.query.get('video')
    video = await clipyweb.request.get_video(video_url)
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
    index = int(request.query.get('index'))
    vid = request.query.get('vid')
    video = await clipyweb.request.get_video(vid)
    stream = video.streams[index]
    actives = request.app['actives']
    actives.append(stream.url)
    data = await clipyweb.download.get(stream, actives, log=sys.stdout)

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
