import aiohttp
import aiohttp_jinja2
import jinja2

from clipyweb.routes import setup_routes


async def cleanup(app):
    pass

app = aiohttp.web.Application()
setup_routes(app)
aiohttp_jinja2.setup(app, loader=jinja2.PackageLoader('clipyweb', 'templates'))
app.router.add_static('/static/', path='static', name='static')
app.on_cleanup.append(cleanup)
aiohttp.web.run_app(app, host='127.0.0.1', port=7070)
