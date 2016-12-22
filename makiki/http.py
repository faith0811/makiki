# -*- coding: utf-8 -*-

try:
    import hug
except ImportError:
    raise ImportError('To use http module, you must install hug.')

import collections

from .executor import (
    FunctionExecutor,
    simple_http_wrapper,
)


API = collections.namedtuple('API', ['uri', 'method', 'func'])


def default_404_handler(request):
    return simple_http_wrapper(status=404, message='Not Found.')


def generate_http_api(module_name, user_apis, executor, not_found_show_documentation=True, not_found_handler=default_404_handler):
    api = hug.API(module_name)
    for user_api in user_apis:
        hug.http(user_api.uri, accept=[user_api.method], api=api)(executor(user_api.func))
    if not not_found_show_documentation:
        hug.not_found()(not_found_handler)
    return api
