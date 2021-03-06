import os

import redis
from pyramid.config import Configurator

from push_messages.db import resolve_elasticache_node


__version__ = "0.7"


def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    # Load a default aws default region
    if "AWS_DEFAULT_REGION" not in os.environ:
        os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

    # Env overrides
    elasticache = os.environ.get("REDIS_ELASTICACHE",
                                 settings.get("redis_elasticache"))
    if elasticache:
        redis_host = resolve_elasticache_node(elasticache)
    else:
        redis_host = os.environ.get("REDIS_HOST", settings['redis_host'])
    redis_port = int(os.environ.get("REDIS_PORT", "6379"))
    redis_db = int(os.environ.get("REDIS_DB", settings['redis_db']))

    redis_server = redis.StrictRedis(
        host=redis_host,
        port=redis_port,
        db=redis_db,
    )

    settings["pyramid_swagger.exclude_paths"] = [
        r"^/__version__",
        r"^/__heartbeat__",
        r"^/__lbheartbeat__",
    ]

    # Provide a redis server instance off the request
    def rs(request):
        return redis_server

    if 'debug' in settings:
        settings['pyramid_swagger.exclude_routes'] = ['debugtoolbar']
    config = Configurator(settings=settings)
    config.registry.redis_server = redis_server
    config.add_request_method(rs, 'redis', reify=True)

    config.include('pyramid_swagger')

    config.add_route('get_keys', '/keys', request_method='GET')
    config.add_route('register_key', '/keys', request_method='POST')
    config.add_route('delete_key', '/keys/{key}', request_method='DELETE')
    config.add_route('get_messages', '/messages/{key}', request_method='GET')

    # Healthcheck views
    config.add_route("version", "/__version__", request_method="GET")
    config.add_route("heartbeat", "/__heartbeat__", request_method="GET")
    config.add_route("lbheartbeat", "/__lbheartbeat__", request_method="GET")

    config.scan(".views")
    return config.make_wsgi_app()
