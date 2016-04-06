import boto3
from boto3.dynamodb.conditions import Key


def resolve_elasticache_node(cache_name):
    es_client = boto3.client('elasticache')
    # Locate elasticache instance, bail if not ready
    result = es_client.describe_cache_clusters(
        CacheClusterId=cache_name,
        ShowCacheNodeInfo=True,
    )
    if not result["CacheClusters"]:
        raise Exception("No cache cluster found of id: %s" % cache_name)
    cluster = result["CacheClusters"][0]
    return cluster["CacheNodes"][0]["Endpoint"]["Address"]


def create_key_table(dynamodb, tablename):
    table = dynamodb.create_table(
        TableName=tablename,
        KeySchema=[
            {
                'AttributeName': 'options',
                'KeyType': 'HASH',
            },
            {
                'AttributeName': 'pubkey',
                'KeyType': 'RANGE'
            }
        ],
        AttributeDefinitions=[
            {
                'AttributeName': 'options',
                'AttributeType': 'S'
            },
            {
                'AttributeName': 'pubkey',
                'AttributeType': 'S'
            }
        ],
        ProvisionedThroughput={
            'ReadCapacityUnits': 5,
            'WriteCapacityUnits': 5
        }
    )
    table.meta.client.get_waiter('table_exists').wait(TableName=tablename)
    return table


def make_table_or_return(dynamodb, tablename):
    table_names = [x.name for x in dynamodb.tables.all()]
    if tablename in table_names:
        return dynamodb.Table(tablename)
    else:
        return create_key_table(dynamodb, tablename)


class KeyResource(object):
    def __init__(self, tablename, autocreate=True, db_options=None):
        db_opts = db_options or {}
        dynamodb = boto3.resource("dynamodb", **db_opts)
        self._tablename = tablename
        if autocreate:
            self._table = make_table_or_return(dynamodb, tablename)
        else:
            self._table = dynamodb.Table(tablename)

    def all_keys(self):
        response = self._table.query(
            KeyConditionExpression=Key('options').eq('public_keys')
        )
        return response['Items']

    def register_key(self, key):
        self._table.put_item(
            Item=dict(options='public_keys', pubkey=key)
        )

    def delete_key(self, key):
        self._table.delete_item(
            Key=dict(options='public_keys', pubkey=key)
        )
