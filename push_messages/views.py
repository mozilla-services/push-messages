import json

from pyramid.exceptions import NotFound
from pyramid.response import Response
from pyramid.view import view_config

import push_messages


@view_config(route_name='get_keys', renderer='json')
def get_keys(request):
    return dict(keys=[{'public-key': v} for v in
                      request.redis.hkeys("registered_keys")])


@view_config(route_name='register_key')
def register_key(request):
    public_key = request.swagger_data['key']['public-key']
    request.redis.hset("registered_keys", public_key, "")
    loc = '/'.join([request.host_url, "keys", public_key])
    return Response(status=201, headers={'Location': str(loc)})


@view_config(route_name='delete_key')
def delete_key(request):
    key = request.matchdict['key']
    request.redis.hdel("registered_keys", key)
    return Response(status=204)


@view_config(route_name='get_messages', renderer='json')
def get_messages(request):
    public_key = request.matchdict['key']
    if not request.redis.hexists("registered_keys", public_key):
        raise NotFound()

    messages = request.redis.lrange(public_key, 0, 200)
    messages = filter(None, messages)
    loaded_messages = [json.loads(message) for message in messages]
    if not messages:
        return Response(status=204)
    return {
        'messages': [
            {'id': m['id'],
             'timestamp': float(m['timestamp']),
             'size': int(m['size']),
             'ttl': int(m['ttl'])} for m in loaded_messages
        ]
    }


@view_config(context="pyramid.exceptions.NotFound")
def empty_404(request):
    return Response("", status_code=404)


# Health-check views

@view_config(route_name="version", renderer="json")
def version(request):
    return dict(
        source="https://github.com/mozilla-services/push-messages/",
        version=push_messages.__version__,
        commit="",
    )


@view_config(route_name="heartbeat", renderer="json")
def heartbeat(request):
    request.key_table.all_keys()
    request.redis.lrange("dummykey", 0, 10)
    return {}


@view_config(route_name="lbheartbeat", renderer="json")
def lbheartbeat(request):
    return {}
