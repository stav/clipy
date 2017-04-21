import asyncio
# import logging

import aiohttp.web
import aiohttp_jinja2
import jinja2

from clipyweb.routes import setup_routes

# config = parse_yaml('logger.yml') # => turns config.yml to dict
# logging.config.dictConfig(config['logging'])
# logger = logging.getLogger('clipy')


async def cleanup(app):
    pass

app = aiohttp.web.Application(
    loop=asyncio.get_event_loop(),
    # logger=logger,
)
app['actives'] = list()
setup_routes(app)
aiohttp_jinja2.setup(app, loader=jinja2.PackageLoader('clipyweb', 'templates'))
app.router.add_static('/static/', path='static', name='static')
app.on_cleanup.append(cleanup)
