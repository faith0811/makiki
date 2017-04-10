
import psycogreen.gevent

import functools
import json
import hug.interface

import hug._empty as empty

from cgi import parse_header
from collections import OrderedDict
from hug.types import text

original_wraps = functools.wraps


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


# def documentation(self, add_to=None):
#     """Produces general documentation for the interface"""
#     doc = OrderedDict if add_to is None else add_to
#
#     usage = self.interface.spec.__doc__
#     if 'return' in self.interface.spec.__annotations__:
#         doc['output_example'] = make_resp(json.loads(json.dumps(self.interface.spec.__annotations__['return'], default=encode_types)))
#     if usage:
#         doc['usage'] = usage
#     if getattr(self, 'requires', None):
#         doc['requires'] = [getattr(requirement, '__doc__', requirement.__name__) for requirement in self.requires]
#     doc['outputs'] = OrderedDict()
#     doc['outputs']['format'] = self.outputs.__doc__
#     doc['outputs']['content_type'] = self.outputs.content_type
#     parameters = [param for param in self.parameters if param not in (
#         'request', 'response', 'self') and not param.startswith('hug_') and not hasattr(param, 'directive')]
#     if parameters:
#         inputs = doc.setdefault('inputs', OrderedDict())
#         types = self.interface.spec.__annotations__
#         for argument in parameters:
#             kind = types.get(argument, text)
#             if getattr(kind, 'directive', None) is True:
#                 continue
#
#             input_definition = inputs.setdefault(argument, OrderedDict())
#             input_definition['type'] = kind if isinstance(kind, str) else kind.__doc__
#             default = self.defaults.get(argument, None)
#             if default is not None:
#                 input_definition['default'] = default
#
#     return doc


def call_function(self, **parameters):
    """Let request/response got by interface, even the interface has no kwargs.

    :param self:
    :param parameters:
    :return:
    """
    all_parameters = ('request', 'response', *self.all_parameters)
    if not self.interface.takes_kwargs:
        parameters = {key: value for key, value in parameters.items() if key in all_parameters}

    return self.interface(**parameters)


def gather_parameters(self, request, response, api_version=None, **input_parameters):
    """Gathers and returns all parameters that will be used for this endpoint"""
    # Mock the function parameters and add request into it
    if 'request' not in self.parameters:
        self.parameters = tuple(list(self.parameters) + ['request'])
    if 'response' not in self.parameters:
        self.parameters = tuple(list(self.parameters) + ['response'])
    input_parameters.update(request.params)
    if self.parse_body and request.content_length:
        body = request.stream
        content_type, ct_params = parse_header(request.content_type)
        body_formatter = body and self.api.http.input_format(content_type)
        if body_formatter:
            body = body_formatter(body, ct_params) if ct_params else body_formatter(body)
        if 'body' in self.parameters:
            input_parameters['body'] = body
        if isinstance(body, dict):
            input_parameters.update(body)
    elif 'body' in self.parameters:
        input_parameters['body'] = None

    if 'request' in self.parameters:
        input_parameters['request'] = request
    if 'response' in self.parameters:
        input_parameters['response'] = response
    if 'api_version' in self.parameters:
        input_parameters['api_version'] = api_version
    for parameter, directive in self.directives.items():
        arguments = (self.defaults[parameter], ) if parameter in self.defaults else ()
        input_parameters[parameter] = directive(*arguments, response=response, request=request,
                                                api=self.api, api_version=api_version, interface=self)

    return input_parameters


def patch():
    psycogreen.gevent.patch_psycopg()
    functools.wraps = wraps
    # hug.interface.Interface.documentation = documentation
    hug.interface.HTTP.gather_parameters = gather_parameters
    hug.interface.HTTP.call_function = call_function
