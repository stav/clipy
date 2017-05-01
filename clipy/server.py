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


async def run_loop(app):
    while app['server']['running']:
        await asyncio.sleep(2)


def main():

    # with open("logger.yaml", 'r') as stream:
    #     config = yaml.load(stream)
    #     logging.config.dictConfig(config['logging'])

    logging.basicConfig(level=logging.DEBUG)
    # logger = logging.getLogger('access')

    async def on_startup(app):
        logging.debug('@@@ startup')

    async def on_cleanup(app):
        logging.debug('@@@ cleanup')

    async def on_shutdown(app):
        logging.debug('@@@ shutdown')

    loop = asyncio.get_event_loop()
    loop.set_debug(True)

    # app = aiohttp.web.Application(
    #     # logger=logger,
    #     loop=loop,  # deprecated http://aiohttp.readthedocs.io/en/stable/web_reference.html#aiohttp.web.Application
    # )
    app = aiohttp.web.Application()
    app['actives'] = dict()
    app['server'] = dict(running=True)
    clipy.routes.setup_routes(app)
    aiohttp_jinja2.setup(app, loader=jinja2.PackageLoader('clipy', 'templates'))
    app.router.add_static('/static/', path='static', name='static')
    app.on_startup.append(on_startup)
    app.on_cleanup.append(on_cleanup)
    app.on_shutdown.append(on_shutdown)
    # aiohttp.web.run_app(app, host='127.0.0.1', port=7070)

    handler = app.make_handler()
    f = loop.create_server(handler, '0.0.0.0', 7070)
    srv = loop.run_until_complete(f)
    print('serving on', srv.sockets[0].getsockname())
    try:
        # loop.run_forever()
        loop.run_until_complete(run_loop(app))
    except Exception as e:
        logging.error(e)
    finally:
        srv.close()
        loop.run_until_complete(srv.wait_closed())
        loop.run_until_complete(app.shutdown())
        loop.run_until_complete(handler.shutdown(60.0))
        loop.run_until_complete(app.cleanup())

    loop.close()


if __name__ == "__main__":
    main()
