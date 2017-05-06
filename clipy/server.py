"""
https://docs.python.org/3/library/asyncio-dev.html#asyncio-debug-mode

Enable the asyncio debug mode globally by setting the environment variable PYTHONASYNCIODEBUG to 1, or by calling AbstractEventLoop.set_debug().

Set the log level of the asyncio logger to logging.DEBUG. For example, call logging.basicConfig(level=logging.DEBUG) at startup.

Configure the warnings module to display ResourceWarning warnings. For example, use the -Wdefault command line option of Python to display them.
"""
import asyncio
import logging
# import logging.config

import aiohttp.web
import aiohttp_jinja2
import jinja2
# import yaml

import clipy.routes

loop = asyncio.get_event_loop()
loop.set_debug(True)


class PollFilter(logging.Filter):
    def filter(self, record):
        return not record.getMessage().startswith('poll')


# with open("logger.yaml", 'r') as stream:
#     config = yaml.load(stream)
#     logging.config.dictConfig(config['logging'])

logging.basicConfig(level=logging.DEBUG)

asyncio_logger = logging.getLogger('asyncio')
asyncio_logger.setLevel(logging.INFO)
asyncio_logger.addFilter(PollFilter())

# downloader_logger = logging.getLogger('clipy:downloader')
logger = logging.getLogger('clipy.server')
# views_logger = logging.getLogger('clipy:views')


def init(app):
    app['server'] = dict()
    app['actives'] = dict()
    clipy.routes.setup_routes(app)
    aiohttp_jinja2.setup(app, loader=jinja2.PackageLoader('clipy', 'templates'))
    app.router.add_static('/static/', path='static', name='static')
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    app.on_shutdown.append(on_shutdown)


async def on_startup(app):
    logger.info(f'startup: {app}')

    def get_server_uri():
        socket = app['server']['sockets'][0]
        host, port = socket.getsockname()
        return 'http://{}:{}/'.format(host, port)

    app['server']['running'] = True
    uri = get_server_uri()
    logger.info(f'serving on {uri}')


async def on_shutdown(app):
    logger.info(f'shutdown: {app}')


async def on_cleanup(app):
    logger.info(f'cleanup: {app}')
    app['actives'].clear()
    app['server'].clear()


async def run_loop(app):
    while app['server']['running']:
        await asyncio.sleep(2)


def main():
    app = aiohttp.web.Application(
        debug=True,
        # logger=logger,
        # loop=loop,  # deprecated http://aiohttp.readthedocs.io/en/stable/web_reference.html#aiohttp.web.Application
    )
    # aiohttp.web.run_app(app, host='127.0.0.1', port=7070)
    init(app)
    handler = app.make_handler(loop=loop)
    f = loop.create_server(handler, '127.0.0.1', 7070)
    srv = loop.run_until_complete(f)
    app['server']['sockets'] = srv.sockets
    try:
        loop.run_until_complete(app.startup())
        loop.run_until_complete(run_loop(app))
    except Exception as e:
        logging.error(e)
    except KeyboardInterrupt:
        logger.warning(f'Interrupt')
    finally:
        srv.close()
        loop.run_until_complete(srv.wait_closed())
        loop.run_until_complete(app.shutdown())
        loop.run_until_complete(handler.shutdown(60.0))
        loop.run_until_complete(app.cleanup())

    loop.close()


if __name__ == "__main__":
    main()
