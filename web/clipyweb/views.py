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
    # data = await clipyweb.download.get(stream, request.app['actives'], log=sys.stdout)
    data = dict(
        message='Queued',
        stream=stream.url,
        index=index,
        video=video.detail,
        vid=vid,
    )
    # run download as task in background
    download = clipyweb.download.get(stream, request.app['actives'], log=sys.stdout)
    request.app.loop.create_task(download)

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
