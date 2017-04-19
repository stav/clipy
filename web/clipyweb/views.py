import json

import aiohttp
import aiohttp_jinja2
# import pafy

import clipyweb

VIDEO_URL = 'https://www.youtube.com/watch?v=-gZOxddqjjw'


async def test(request):
    # try:
    #     video = pafy.new(request.query['video'])
    # except (OSError, ValueError) as e:
    #     data = dict(
    #         error=str(e),
    #     )
    # else:
    video = await clipyweb.info(VIDEO_URL)
    data = dict(
        description=video.description,
        duration=video.duration,
        streams=[str(s) for s in video.streams],
        title=video.title,
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
