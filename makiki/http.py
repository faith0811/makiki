# -*- coding: utf-8 -*-

try:
    import hug
except ImportError:
    raise ImportError('To use http module, you must install hug.')

import functools
import gevent
import collections

from .executor import FunctionExecutor


API = collections.namedtuple('API', ['uri', 'method', 'func'])


def simple_http_wrapper(data=None, status=200, message='Success', code=0):
    return {
        'meta': {
            'code': code,
            'status': status,
            'message': message,
        },
        'data': data,
    }


def default_404_handler(request):
    return simple_http_wrapper(status=404, message='Not Found.')


def generate_http_api(module_name, user_apis, executor, not_found_show_documentation=True, not_found_handler=default_404_handler):
    api = hug.API(module_name)
    for user_api in user_apis:
        hug.http(user_api.uri, accept=[user_api.method], api=api)(executor(user_api.func))
    if not not_found_show_documentation:
        hug.not_found()(not_found_handler)
    return api


class TimeoutWrapper(object):

    def __init__(self, app, timeout=15):
        self.app = app
        self.timeout = timeout

    def __call__(self, *args, **kwargs):
        with gevent.Timeout(self.timeout):
            return self._gevent_wrapper(self.app)(*args, **kwargs)

    def __getattr__(self, key):
        return getattr(self.app, key)

    @staticmethod
    def _gevent_wrapper(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            task = gevent.spawn(func, *args, **kwargs)
            task.join()
            if not task.successful():
                raise task.exception
            return task.value
        return wrapper
