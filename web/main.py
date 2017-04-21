import aiohttp.web

from clipyweb import app


if __name__ == "__main__":
    aiohttp.web.run_app(app, host='127.0.0.1', port=7070)
