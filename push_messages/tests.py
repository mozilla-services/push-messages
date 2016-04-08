import boto3
import json
import logging
import os
import psutil
import signal
import subprocess
import time
import uuid
import unittest
from unittest.case import SkipTest

from mock import Mock, patch
from nose.tools import eq_, ok_, raises
from pyramid import testing


log = logging.getLogger(__name__)
here_dir = os.path.abspath(os.path.dirname(__file__))
root_dir = os.path.dirname(here_dir)
ddb_dir = os.path.join(root_dir, "ddb")
ddb_lib_dir = os.path.join(ddb_dir, "DynamoDBLocal_lib")
ddb_jar = os.path.join(ddb_dir, "DynamoDBLocal.jar")
ddb_process = None


def setUp():
    boto3.setup_default_session()
    logging.getLogger('boto').setLevel(logging.CRITICAL)
    if "SKIP_INTEGRATION" in os.environ:  # pragma: nocover
        raise SkipTest("Skipping integration tests")
    global ddb_process
    cmd = " ".join([
        "java", "-Djava.library.path=%s" % ddb_lib_dir,
        "-jar", ddb_jar, "-sharedDb", "-inMemory"
    ])
    ddb_process = subprocess.Popen(cmd, shell=True, env=os.environ)


def tearDown():
    global ddb_process
    # This kinda sucks, but its the only way to nuke the child procs
    proc = psutil.Process(pid=ddb_process.pid)
    child_procs = proc.children(recursive=True)
    for p in [proc] + child_procs:
        os.kill(p.pid, signal.SIGTERM)
    ddb_process.wait()


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
            "dynamodb_key_table": "push_messages_db",
            "pyramid_swagger.schema_directory": ".",
            "pyramid_swagger.schema_file": "push_api.yaml",
            "debug": "true",
            "local_dynamodb": "true"
        })
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

    @patch("push_messages.resolve_elasticache_node")
    def test_wsgi_app_with_elasticache(self, mock_resolve):
        from push_messages import main
        from webtest import TestApp
        app = main({}, **{
            "redis_elasticache": "acachename",
            "redis_db": 0,
            "dynamodb_key_table": "push_messages_db",
            "pyramid_swagger.schema_directory": ".",
            "pyramid_swagger.schema_file": "push_api.yaml",
            "debug": "true",
            "local_dynamodb": "true"
        })
        testapp = TestApp(app)
        result = testapp.get("/keys", status=200)
        data = json.loads(result.body)
        eq_(data["keys"], [])
        eq_(len(mock_resolve.mock_calls), 1)

    def test_get_keys(self):
        from .views import get_keys
        request = testing.DummyRequest()
        request.key_table = Mock()
        request.key_table.all_keys.return_value = [
            dict(pubkey="asdf")
        ]
        info = get_keys(request)
        eq_(info["keys"][0]["public-key"], "asdf")

    def test_post_key(self):
        from .views import register_key
        request = testing.DummyRequest()
        request.key_table = Mock()
        request.swagger_data = dict(key={"public-key": "asdf"})
        info = register_key(request)
        eq_(info.status_code, 201)

    def test_delete_key(self):
        from .views import delete_key
        request = testing.DummyRequest()
        request.key_table = Mock()
        request.matchdict = dict(key="asdf")
        info = delete_key(request)
        eq_(info.status_code, 204)

    def test_get_messages(self):
        from .views import get_messages
        request = testing.DummyRequest()
        request.matchdict["key"] = "something"
        request.redis = Mock()
        request.redis.lrange.return_value = [
            json.dumps(dict(id=2, timestamp=7894721893,
                            size=313, ttl=200))
        ]
        info = get_messages(request)
        eq_(len(info["messages"]), 1)

    def test_version(self):
        from .views import version
        request = testing.DummyRequest()
        info = version(request)
        eq_(len(info), 3)

    def test_heartbeat(self):
        from .views import heartbeat
        request = testing.DummyRequest()
        request.redis = Mock()
        request.key_table = Mock()
        info = heartbeat(request)
        eq_(len(request.redis.mock_calls), 1)
        eq_(len(request.key_table.mock_calls), 1)
        eq_(info, {})

    def test_lbheartbeat(self):
        from .views import lbheartbeat
        request = testing.DummyRequest()
        info = lbheartbeat(request)
        eq_(info, {})


class DbTests(unittest.TestCase):
    def _makeFUT(self, *args, **kwargs):
        from push_messages.db import KeyResource
        kwargs["db_options"] = dict(
            endpoint_url="http://localhost:8000",
            region_name="us-east-1", verify=False,
            aws_access_key_id="", aws_secret_access_key=""
        )
        return KeyResource(*args, **kwargs)

    def test_create(self):
        kr = self._makeFUT("push_messages")
        eq_(kr.all_keys(), [])

        # Repeat call as the table name will match this time
        kr = self._makeFUT("push_messages")
        eq_(kr.all_keys(), [])

        krs = self._makeFUT("push_messages", autocreate=False)
        eq_(krs.all_keys(), [])

    def test_reg_and_delete(self):
        kr = self._makeFUT("push_messages")
        kr.register_key("asdf")
        ok_("asdf" in [x["pubkey"] for x in kr.all_keys()])

        kr.delete_key("asdf")
        eq_(kr.all_keys(), [])

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
