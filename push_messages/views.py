import json

from pyramid.exceptions import NotFound
from pyramid.response import Response
from pyramid.view import view_config

import push_messages


@view_config(route_name='get_keys', renderer='json')
def get_keys(request):
    return dict(keys=[{'public-key': x['pubkey']} for x in
                      request.key_table.all_keys()])


@view_config(route_name='register_key')
def register_key(request):
    key = request.swagger_data['key']['public-key']
    request.key_table.register_key(key)
    loc = '/'.join([request.host_url, "keys", key])
    return Response(status=201, headers={'Location': str(loc)})


@view_config(route_name='delete_key')
def delete_key(request):
    key = request.matchdict['key']
    request.key_table.delete_key(key)
    return Response(status=204)


@view_config(route_name='get_messages', renderer='json')
def get_messages(request):
    messages = request.redis.lrange(request.matchdict['key'], 0, 200)
    messages = filter(None, messages)
    if not messages:
        raise NotFound()
    loaded_messages = [json.loads(message) for message in messages]
    return {
        'messages': [
            {'id': m['id'],
             'timestamp': float(m['timestamp']),
             'size': int(m['size']),
             'ttl': int(m['ttl'])} for m in loaded_messages
        ]
    }


# Healthcheck views

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
