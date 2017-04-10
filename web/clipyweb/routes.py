from clipyweb.views import index, test


def setup_routes(app):
    app.router.add_get('/', index)
    app.router.add_get('/api/test', test)
