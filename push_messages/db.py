import boto3
from boto3.dynamodb.conditions import Key

try:
    dynamodb = boto3.resource('dynamodb')
except:
    dynampdb = None


def create_key_table(tablename):
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


def make_table_or_return(tablename):
    table_names = [x.name for x in dynamodb.tables.all()]
    if tablename in table_names:
        return dynamodb.Table(tablename)
    else:
        return create_key_table(tablename)


class KeyResource(object):
    def __init__(self, tablename, autocreate=True):
        self._tablename = tablename
        if autocreate:
            self._table = make_table_or_return(tablename)
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
