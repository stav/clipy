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
    stream_index = int(request.query.get('stream'))
    vid = request.query.get('vid')
    video = await clipyweb.request.get_video(vid)
    stream = video.streams[stream_index]
    data = dict(
        message='Queued',
        index=stream_index,
        video=video.detail,
        url=stream.url,
        vid=vid,
    )
    # run download as task in background
    download = clipyweb.download.get(stream, request.app['actives'])
    request.app.loop.create_task(download)

    return aiohttp.web.Response(
        content_type='application/json',
        text=json.dumps(data),
    )


async def progress(request):
    # for stream in request.app['actives'].values():
    #     d = s.progress
    data = dict(
        actives=[{**s.progress, **dict(url=s.url, name=s.name)} for s in request.app['actives'].values()],
    )
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
