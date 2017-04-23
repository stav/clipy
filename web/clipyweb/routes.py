from clipyweb.views import index, inquire, download, progress


def setup_routes(app):
    app.router.add_get('/', index)
    app.router.add_get('/api/inquire', inquire)
    app.router.add_get('/api/download', download)
    app.router.add_get('/api/progress', progress)
