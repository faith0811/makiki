# -*- coding: utf-8 -*-

import collections


Identity = collections.namedtuple('Identity', ['code', 'error_msg', 'http_code'])


class BasicUserException(Exception):
    pass


class Unauthorized(BasicUserException):
    identity = Identity(code=0, error_msg='Unauthorized', http_code=401)


def patch_exc(exc):
    for k, v in exc.__dict__.items():
        if not k.startswith('_'):
            setattr(exc, k, type(k, (exc, ), {'identity': Identity(*v)}))
