# -*- coding: utf-8 -*-

import sys
import logging
import functools
import time
import falcon
import blinker
import gevent

from gevent.hub import get_hub

from .exception import (
    BasicUserException,
    Unauthorized,
)

hub = get_hub()
hub.NOT_ERROR = tuple(list(hub.NOT_ERROR) + [falcon.http_status.HTTPStatus])


class FunctionExecutor(object):

    def __init__(self, http_wrapper=None, sentry_client=None, auth_func=None, log_exclude_fields=None, identity_func=None, log_error=False, thrift_wrapper=None):
        self.has_http_wrapper = bool(http_wrapper)
        self.http_wrapper = http_wrapper if http_wrapper else lambda d, s, m, c: d
        self.thrift_wrapper = thrift_wrapper
        self.sentry_client = sentry_client
        self.auth_func = auth_func if auth_func else lambda req, func: True
        self.log_exclude_fields = log_exclude_fields if log_exclude_fields is not None else {}
        self.identity_func = identity_func
        self.log_error = log_error

    def _http_wrapper(self, data=None, status=200, message='Success', code=0, response=None):
        if response:
            response.status = getattr(falcon, 'HTTP_{}'.format(status))
        return self.http_wrapper(data, status, message, code)

    def _process(self, func, args, kwargs, request, response):
        start_sig = blinker.signal('BeforeFunctionExecute')
        start_sig.send(request)

        if not self.auth_func(request, func):
            raise Unauthorized

        if self.thrift_wrapper:
            return self.thrift_wrapper(func(*args, **kwargs))
        return self._http_wrapper(data=func(*args, **kwargs))

    def _send_sentry_exc(self, request, args, kwargs):
        if self.sentry_client:
            if request:
                self.sentry_client.http_context({
                    'url': request.url,
                    'query_string': request.query_string,
                    'method': request.method,
                    'headers': request.headers,
                })
            self.sentry_client.extra_context({
                'args': args,
                'kwargs': kwargs,
            })
            self.sentry_client.captureException()

    def _prepare_log(self, func_name, args, kwargs, execution_time, request):
        if self.identity_func:
            kwargs['unique_identity'] = self.identity_func(request)
        kwargs_list = []
        for k, v in kwargs.items():
            if k not in self.log_exclude_fields:
                if isinstance(v, str):
                    v = "'{}'".format(v)
                kwargs_list.append('{}={}'.format(k, v))
        args_str = [str(a) for a in args] + kwargs_list
        return '{}({}) response {}ms'.format(
            func_name, ', '.join(args_str), execution_time)

    def _process_exception_output(self, e, func_logger, request, response, args, kwargs):
        if self.has_http_wrapper:
            if isinstance(e, BasicUserException):
                return self._http_wrapper(
                    status=e.identity.http_code,
                    code=e.identity.code,
                    message=e.identity.error_msg,
                    response=response,
                )
            else:
                self._send_sentry_exc(request, args, kwargs)
                if self.log_error:
                    func_logger.exception(e)
                return self._http_wrapper(
                    status=500,
                    code=0,
                    message='Internal Server Error',
                    response=response,
                )
        else:
            if not isinstance(e, BasicUserException):
                self._send_sentry_exc(request, args, kwargs)
            raise

    def _finish_exec(self, duration, func_logger, args, kwargs, request, func):
        end_sig = blinker.signal('AfterFunctionExecute')
        end_sig.send(request)
        func_logger.info(self._prepare_log(func.__name__, args, kwargs, duration, request))

    def __call__(self, func):
        func_logger = logging.getLogger(func.__module__)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start = time.time()
            request = kwargs.get('request')
            if request:
                _of = getattr(func, 'original', func)
                if 'request' not in _of.__code__.co_varnames:
                    del kwargs['request']
            response = kwargs.get('response')
            if response:
                _of = getattr(func, 'original', func)
                if 'response' not in _of.__code__.co_varnames:
                    del kwargs['response']
            try:
                return self._process(func, args, kwargs, request, response)
            except falcon.http_status.HTTPStatus:
                raise
            except Exception as e:
                return self._process_exception_output(e, func_logger, request, response, args, kwargs)
            finally:
                execution_time = (time.time() - start) * 1000
                self._finish_exec(execution_time, func_logger, args, kwargs, request, func)
        return wrapper
