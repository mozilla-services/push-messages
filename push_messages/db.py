import boto3


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
