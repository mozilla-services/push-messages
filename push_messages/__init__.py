import redis
from pyramid.config import Configurator
from pyramid.response import Response

from push_messages.db import KeyResource


def empty_404(request):
    return Response("", status_code=404)


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    redis_server = redis.StrictRedis(
        host=settings['redis_host'],
        port=6379,
        db=int(settings['redis_db'])
    )

    # Provide a redis server instance off the request
    def rs(request):
        return redis_server

    key_resource = KeyResource(settings['dynamodb_key_table'])

    def key_table(request):
        return key_resource

    if 'debug' in settings:
        settings['pyramid_swagger.exclude_routes'] = ['debugtoolbar']
    config = Configurator(settings=settings)
    config.add_request_method(rs, 'redis', reify=True)
    config.add_request_method(key_table, reify=True)

    config.add_view(empty_404, context="pyramid.exceptions.NotFound")

    config.include('pyramid_swagger')

    config.add_route('get_keys', '/keys', request_method='GET')
    config.add_route('register_key', '/keys', request_method='POST')
    config.add_route('delete_key', '/keys/{key}', request_method='DELETE')
    config.add_route('get_messages', '/messages/{key}', request_method='GET')

    config.scan(".views")
    return config.make_wsgi_app()
