import aiohttp.web

import clipy.bootstrap

if __name__ == "__main__":
    app = clipy.bootstrap.app()
    aiohttp.web.run_app(app, host='127.0.0.1', port=7070)
