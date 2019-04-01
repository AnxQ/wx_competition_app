import uuid

from redis import StrictRedis, ResponseError

from config import current_config

redis = StrictRedis.from_url(current_config.RedisURL)
expire = 7 * 24 * 60 * 60


def get_login_openid(uuid):
    try:
        openid = redis.hmget(f'US:{uuid}', 'openid')
    except ResponseError:
        return None
    return openid[0]


def new_login_session(openid, session_key):
    new_uuid = str(uuid.uuid4())
    with redis.pipeline(transaction=False) as pipe:
        pipe.hmset(f'US:{new_uuid}', {'openid': openid, 'session_key': session_key})
        pipe.expire(f'US:{new_uuid}', expire)
        pipe.execute()
    return new_uuid


def clear_redis():
    redis.flushall()
