import logging

import aiohttp.web
import aiohttp_jinja2

import clipy.request
import clipy.download

from clipy.agents.utils import lookup_agent, get_agent

logger = logging.getLogger(__name__)


@aiohttp_jinja2.template('index.html')
async def index(request):
    return {
        'question': 'question',
        'choices': 'choices'
    }


async def inquire(request):
    video_url = request.query.get('video')
    agent = lookup_agent(video_url)
    logger.debug(f'inquire - Agent: {agent}')
    video = await agent.get_video()
    data = dict(
        description=video.description,
        duration=video.duration,
        streams=[s.serial for s in video.streams],
        title=video.title,
        vid=video.vid,
    )
    return aiohttp.web.json_response(data)


async def download(request):
    vid = request.query.get('vid')
    idx = request.query.get('stream')
    agent = get_agent(vid)
    logger.debug(f'download - Agent: {agent}')
    stream = await agent.get_stream(idx)
    # run download as task in background
    coroutine = clipy.download.get(stream, request.app['actives'])
    request.app.loop.create_task(coroutine)
    data = dict(
        message='Queued',
        stream=str(stream),
    )
    return aiohttp.web.json_response(data)


async def progress(request):
    def active(stream):
        info = dict(stream.__dict__)
        info.update(eta=int(stream.eta), rate=int(stream.rate))
        info.update(**info['progress'])
        del info['progress']
        return info
    data = dict(
        actives=[active(s) for s in request.app['actives'].values()],
    )
    return aiohttp.web.json_response(data)


async def cancel(request):
    sid = request.query.get('sid')
    actives = request.app['actives']
    if sid in actives:
        del actives[sid]
        removed = True
    else:
        removed = False
    logger.debug(f'cancel: sid {sid} removed? {removed}')
    data = dict(removed=removed)
    return aiohttp.web.json_response(data)


async def shutdown(request):
    request.app['server']['running'] = False
    data = dict(app=str(request.app))
    return aiohttp.web.json_response(data)
