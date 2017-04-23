"""
https://docs.python.org/3/library/asyncio-dev.html#asyncio-debug-mode

Enable the asyncio debug mode globally by setting the environment variable PYTHONASYNCIODEBUG to 1, or by calling AbstractEventLoop.set_debug().

Set the log level of the asyncio logger to logging.DEBUG. For example, call logging.basicConfig(level=logging.DEBUG) at startup.

Configure the warnings module to display ResourceWarning warnings. For example, use the -Wdefault command line option of Python to display them.
"""
import asyncio
import logging
import logging.config

import aiohttp.web
import aiohttp_jinja2
import jinja2
# import yaml

import clipyweb.routes


def app():

    # with open("logger.yaml", 'r') as stream:
    #     config = yaml.load(stream)
    #     logging.config.dictConfig(config['logging'])

    logging.basicConfig(level=logging.DEBUG)
    # logger = logging.getLogger('access')

    async def startup(app):
        pass

    async def cleanup(app):
        pass

    loop = asyncio.get_event_loop()
    loop.set_debug(True)

    app = aiohttp.web.Application(
        # logger=logger,
        loop=loop,  # deprecated http://aiohttp.readthedocs.io/en/stable/web_reference.html#aiohttp.web.Application
    )
    app['actives'] = dict()
    clipyweb.routes.setup_routes(app)
    aiohttp_jinja2.setup(app, loader=jinja2.PackageLoader('clipyweb', 'templates'))
    app.router.add_static('/static/', path='static', name='static')

    app.on_startup.append(startup)
    app.on_cleanup.append(cleanup)

    return app
