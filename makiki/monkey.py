
import psycogreen.gevent

import functools
import json
import hug.interface

import hug._empty as empty

from cgi import parse_header
from collections import OrderedDict
from hug.types import text

original_wraps = functools.wraps
original_call_function = hug.interface.HTTP.call_function


def wraps(function):
    """Enables building decorators around functions used for hug routes without chaninging their function signature"""
    def wrap(decorator):
        decorator = original_wraps(function)(decorator)
        if not hasattr(function, 'original'):
            decorator.original = function
        else:
            decorator.original = function.original
        return decorator
    return wrap


def call_function(self, **parameters):
    """Let request/response got by interface, even the interface has no kwargs.

    :param self:
    :param parameters:
    :return:
    """
    self.all_parameters = ('request', 'response', *self.all_parameters)
    return original_call_function(self, **parameters)


def patch():
    psycogreen.gevent.patch_psycopg()
    functools.wraps = wraps
    hug.interface.HTTP.call_function = call_function
