from wsgiref.simple_server import make_server
from pyramid.config import Configurator
from pyramid.response import Response


APP_SETTINGS = {
    'pyramid_swagger.schema_directory': ".",
    'pyramid_swagger.schema_file': "push_api.yaml"
}


def get_keys(request):
    return dict(keys=[])


def get_messages(request):
    key = request.matchdict['key']
    return dict(messages=[])


def main(global_conf, **settings):
    config = Configurator(settings=settings)
    config.include('pyramid_swagger')
    config.add_route('get_keys', '/keys', request_method='GET')
    config.add_route('get_messages', '/messages/{key}', request_method='GET')

    config.add_view(get_keys, route_name='get_keys', renderer='json')
    config.add_view(get_messages, route_name='get_messages', renderer='json')
    return config.make_wsgi_app()


if __name__ == '__main__':
    app = main({}, **APP_SETTINGS)
    server = make_server('0.0.0.0', 8080, app)
    server.serve_forever()
