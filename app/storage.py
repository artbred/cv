import json
import time

import redis
from redis.commands.search.field import TextField, VectorField
from redis.commands.search.query import Query
from settings import dim, redis_host, redis_port

downloads_by_label_id_set_key = "downloads_by_label_id"
query_positions_set_key = "query_positions"
utm_params_set_prefix_key = "utm_params:"

labels_prefix_key = "labels:"
vector_field_name = "embedding"
vector_field_name_index = "id"

jwt_set_key = "revoked_tokens"


redis_pool = redis.ConnectionPool(host=redis_host, port=redis_port, db=0)  # decode_responses=True


def create_redis_connection():
    return redis.StrictRedis(connection_pool=redis_pool)


def redis_connection_decorator(func):
    def wrapper(*args, **kwargs):
        conn = create_redis_connection()
        try:
            return func(*args, conn=conn, **kwargs)
        finally:
            conn.close()

    return wrapper


@redis_connection_decorator
def save_utm_params(path, params_str, conn: redis.StrictRedis = None):
    timestamp=int(time.time())

    key = f"{utm_params_set_prefix_key}{path}"
    data = {"timestamp": timestamp, "utm_params": params_str}
    conn.zadd(key, {json.dumps(data): timestamp})


@redis_connection_decorator
async def save_query_position(positon: str, score: float, most_similar_label_id: str, conn: redis.StrictRedis = None):
    timestamp=int(time.time())

    data = {
        "query_position": positon,
        "score": score,
        "most_similar_label_id": most_similar_label_id,
        "timestamp": timestamp,
    }

    conn.zadd(query_positions_set_key, {json.dumps(data): timestamp})


@redis_connection_decorator
async def save_download_by_label_id(label_id: str, utm_source = None, utm_campaign = None, conn: redis.StrictRedis = None):
    timestamp=int(time.time())
    data = {"timestamp": timestamp, "label_id": label_id}

    if utm_source:
        data['utm_source'] = utm_source
    
    if utm_campaign:
        data['utm_campaign'] = utm_campaign

    conn.zadd(downloads_by_label_id_set_key, {json.dumps(data): timestamp})


@redis_connection_decorator
def revoke_jwt_token(token, conn: redis.StrictRedis = None):
    conn.sadd(jwt_set_key, token)


@redis_connection_decorator
def jwt_token_is_revoked(token, conn: redis.StrictRedis = None) -> bool:
    is_revoked = conn.sismember(jwt_set_key, token)
    return is_revoked


@redis_connection_decorator
def save_label_to_redis(label_hash, conn: redis.StrictRedis = None):
    key = label_hash["id"]
    conn.hset(key, mapping=label_hash)


@redis_connection_decorator
def load_label_by_id(key, conn: redis.StrictRedis = None):
    label_hash = conn.hgetall(key)
    return {key.decode(encoding="latin-1"): value.decode(encoding="latin-1") for key, value in label_hash.items()}


@redis_connection_decorator
def query_most_similar_labels(query_embedding, conn: redis.StrictRedis = None, limit=1):
    q = Query(f"*=>[KNN {limit} @{vector_field_name} $vec_param]=>{{$yield_distance_as: dist}}").sort_by(f"dist")
    res = conn.ft().search(q, query_params={"vec_param": query_embedding.tobytes()})

    return res.docs


# Use only if you rewrite class Label or run for first time, clears all data in redis
@redis_connection_decorator
def init_index(conn: redis.StrictRedis = None):
    conn.flushall()

    schema = (
        VectorField(vector_field_name, "FLAT", {"TYPE": "FLOAT32", "DIM": dim, "DISTANCE_METRIC": "COSINE"}),
        TextField(vector_field_name_index),
        TextField("position"),
        TextField("path_to_file"),
        TextField("file_name"),
    )

    conn.ft().create_index(schema)
    conn.ft().config_set("default_dialect", 2)
