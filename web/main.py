import aiohttp.web

import clipyweb.bootstrap

if __name__ == "__main__":
    app = clipyweb.bootstrap.app()
    aiohttp.web.run_app(app, host='127.0.0.1', port=7070)
