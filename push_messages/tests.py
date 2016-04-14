import json
import logging
import time
import uuid
import unittest

from mock import Mock, patch
from nose.tools import eq_, raises
from pyramid import testing
from pyramid.exceptions import NotFound


log = logging.getLogger(__name__)


class ViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_wsgi_app(self):
        from push_messages import main
        from webtest import TestApp
        app = main({}, **{
            "redis_host": "localhost",
            "redis_db": 0,
            "pyramid_swagger.schema_directory": ".",
            "pyramid_swagger.schema_file": "push_api.yaml",
            "debug": "true",
        })
        app.registry.redis_server.delete("registered_keys")
        testapp = TestApp(app)
        result = testapp.get("/keys", status=200)
        data = json.loads(result.body)
        eq_(data["keys"], [])

        result = testapp.get("/messages/fred", status=404)
        eq_(result.body, "")

        # Insert a key
        msg = dict(
            id="asdfasdf",
            ttl="60",
            timestamp=time.time(),
            size=20
        )
        dbkey = uuid.uuid4().hex
        app.registry.redis_server.hset("registered_keys", dbkey, "")
        app.registry.redis_server.lpush(dbkey, json.dumps(msg))

        result = testapp.get("/messages/%s" % dbkey)
        eq_(json.loads(result.body), dict(
            messages=[dict(
                id="asdfasdf",
                ttl=60,
                timestamp=msg["timestamp"],
                size=20
            )]
        ))

        # Verify 204
        app.registry.redis_server.delete(dbkey)
        result = testapp.get("/messages/%s" % dbkey, status=204)
        eq_(result.body, "")

    @patch("push_messages.resolve_elasticache_node")
    def test_wsgi_app_with_elasticache(self, mock_resolve):
        from push_messages import main
        from webtest import TestApp
        mock_resolve.return_value = "localhost"
        app = main({}, **{
            "redis_elasticache": "acachename",
            "redis_db": 0,
            "pyramid_swagger.schema_directory": ".",
            "pyramid_swagger.schema_file": "push_api.yaml",
            "debug": "true",
        })
        app.registry.redis_server.delete("registered_keys")
        testapp = TestApp(app)
        result = testapp.get("/keys", status=200)
        data = json.loads(result.body)
        eq_(data["keys"], [])
        eq_(len(mock_resolve.mock_calls), 1)

    def test_get_keys(self):
        from .views import get_keys
        request = testing.DummyRequest()
        request.redis = Mock()
        request.redis.hkeys.return_value = ["asdf"]
        request.key_table = Mock()
        request.key_table.all_keys.return_value = [
            dict(pubkey="asdf")
        ]
        info = get_keys(request)
        eq_(info["keys"][0]["public-key"], "asdf")

    def test_post_key(self):
        from .views import register_key
        request = testing.DummyRequest()
        request.redis = Mock()
        request.swagger_data = dict(key={"public-key": "asdf"})
        info = register_key(request)
        eq_(info.status_code, 201)
        request.redis.hset.assert_called_with("registered_keys", "asdf", "")

    def test_delete_key(self):
        from .views import delete_key
        request = testing.DummyRequest()
        request.redis = Mock()
        request.matchdict = dict(key="asdf")
        info = delete_key(request)
        eq_(info.status_code, 204)
        request.redis.hdel.assert_called_with("registered_keys", "asdf")

    def test_get_messages(self):
        from .views import get_messages
        request = testing.DummyRequest()
        request.matchdict["key"] = "something"
        request.redis = Mock()
        request.redis.hexists.return_value = True
        request.redis.lrange.return_value = [
            json.dumps(dict(id=2, timestamp=7894721893,
                            size=313, ttl=200))
        ]
        info = get_messages(request)
        eq_(len(info["messages"]), 1)
        request.redis.hexists.assert_called_with("registered_keys",
                                                 "something")

    @raises(NotFound)
    def test_get_messages_404_error(self):
        from .views import get_messages
        request = testing.DummyRequest()
        request.matchdict["key"] = "something"
        request.redis = Mock()
        request.redis.hexists.return_value = False
        get_messages(request)

    def test_get_messages_204(self):
        from .views import get_messages
        request = testing.DummyRequest()
        request.matchdict["key"] = "something"
        request.redis = Mock()
        request.redis.hexists.return_value = True
        request.redis.lrange.return_value = []
        response = get_messages(request)
        eq_(response.status_code, 204)
        request.redis.hexists.assert_called_with("registered_keys",
                                                 "something")

    def test_version(self):
        from .views import version
        request = testing.DummyRequest()
        info = version(request)
        eq_(len(info), 3)

    def test_heartbeat(self):
        from .views import heartbeat
        request = testing.DummyRequest()
        request.redis = Mock()
        info = heartbeat(request)
        eq_(len(request.redis.mock_calls), 1)
        eq_(info, {})

    def test_lbheartbeat(self):
        from .views import lbheartbeat
        request = testing.DummyRequest()
        info = lbheartbeat(request)
        eq_(info, {})


class DbTests(unittest.TestCase):
    @patch("push_messages.db.boto3")
    def test_resolve_elasticache(self, mock_boto):
        from push_messages.db import resolve_elasticache_node
        mock_boto.client.return_value = mock_client = Mock()
        mock_client.describe_cache_clusters.return_value = dict(
            CacheClusters=[
                dict(
                    CacheNodes=[
                        dict(
                            Endpoint=dict(Address="localhost")
                        )
                    ]
                )
            ]
        )
        resolve_elasticache_node("somename")
        eq_(len(mock_client.mock_calls), 1)
        eq_(len(mock_boto.mock_calls), 2)

        # No cluster
        mock_client.describe_cache_clusters.return_value = dict(
            CacheClusters=[]
        )

        @raises(Exception)
        def testit():
            resolve_elasticache_node("somename")
        testit()
