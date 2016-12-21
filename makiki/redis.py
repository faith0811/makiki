# -*- coding: utf-8 -*-

import redis
import functools


class PrefixRedis(object):
    """Redis client add prefix in front of key auto.

    """
    __support_functions__ = ['get', 'set', 'setex', 'hset', 'hget', 'setnx', 'hsetnx', 'expire', 'hmset', 'hmget', 'incr', 'sadd', 'srem']

    def __init__(self, prefix, **config):
        super().__init__()
        self._prefix = prefix
        self._r = redis.StrictRedis(**config)

    def __getattr__(self, key):
        if key not in self.__support_functions__:
            raise AttributeError('Prefix Redis does not have {} function'.format(key))
        return self.prefix_wrapper(getattr(self._r, key))

    def prefix_wrapper(self, func):
        @functools.wraps(func)
        def wrapper(key, *args, **kwargs):
            return func(self._prefix.format(key), *args, **kwargs)
        return wrapper
