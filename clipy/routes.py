from clipy.views import index, inquire, download, progress, cancel, tasks, shutdown


def setup_routes(app):
    app.router.add_get('/', index)
    app.router.add_get('/api/inquire', inquire)
    app.router.add_get('/api/download', download)
    app.router.add_get('/api/progress', progress)
    app.router.add_get('/api/cancel', cancel)
    app.router.add_get('/api/tasks', tasks)
    app.router.add_get('/api/shutdown', shutdown)
