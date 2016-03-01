import json

from pyramid.exceptions import NotFound
from pyramid.response import Response
from pyramid.view import view_config


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
    if not messages:
        raise NotFound()
    loaded_messages = [json.loads(message) for message in messages]
    return {
        'messages': [
            {'id': m['id'],
             'timestamp': m['timestamp'],
             'size': m['size'],
             'ttl': m['ttl']} for m in loaded_messages
        ]
    }
