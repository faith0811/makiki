
import psycogreen.gevent

import functools
import json
import hug.interface

import hug._empty as empty

from cgi import parse_header
from collections import OrderedDict
from hug.types import text

original_wraps = functools.wraps
original_gather_parameters = hug.interface.HTTP.gather_parameters
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
    # Mock the function parameters and add request into it
    self.all_parameters = tuple({'request', 'response', *self.all_parameters})
    return original_call_function(self, **parameters)


def gather_parameters(self, request, response, api_version=None, **input_parameters):
    """Gathers and returns all parameters that will be used for this endpoint"""
    # Mock the function parameters and add request into it
    self.all_parameters = tuple({'request', 'response', *self.all_parameters})
    return original_gather_parameters(self, request, response, api_version, **input_parameters)


def patch():
    psycogreen.gevent.patch_psycopg()
    functools.wraps = wraps
    # hug.interface.Interface.documentation = documentation
    hug.interface.HTTP.gather_parameters = gather_parameters
    hug.interface.HTTP.call_function = call_function
