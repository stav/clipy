import json
import logging

import aiohttp.web
import aiohttp_jinja2

import clipy.request
import clipy.download

logger = logging.getLogger('clipy:views')


@aiohttp_jinja2.template('index.html')
async def index(request):
    return {
        'question': 'question',
        'choices': 'choices'
    }


async def inquire(request):
    video_url = request.query.get('video')
    video = await clipy.request.get_video(video_url)
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
    video = await clipy.request.get_video(vid)
    stream = video.streams[stream_index]
    data = dict(
        message='Queued',
        index=stream_index,
        video=video.detail,
        hash=stream.hash,
        vid=vid,
    )
    # run download as task in background
    coroutine = clipy.download.get(stream, request.app['actives'])
    request.app.loop.create_task(coroutine)

    return aiohttp.web.Response(
        content_type='application/json',
        text=json.dumps(data),
    )


async def progress(request):
    # for stream in request.app['actives'].values():
    #     d = s.progress
    data = dict(
        actives=[{**s.progress, **dict(hash=s.hash, name=s.name)} for s in request.app['actives'].values()],
    )
    return aiohttp.web.Response(
        content_type='application/json',
        text=json.dumps(data),
    )


async def cancel(request):
    hash = request.query.get('hash')
    actives = request.app['actives']
    if hash in actives:
        del actives[hash]
        removed = True
    else:
        removed = False
    logger.debug(f'cancel: hash {hash} removed? {removed}')
    data = dict(removed=removed)
    return aiohttp.web.json_response(data)


async def shutdown(request):
    # app = request.app
    # loop = app.loop
    # loop.run_until_complete(app.shutdown())
    # loop.run_until_complete(app.cleanup())
    # app.shutdown()
    # app.cleanup()
    # raise TypeError('asdf')
    request.app['server']['running'] = False
    data = dict(app=str(request.app))
    return aiohttp.web.json_response(data)
