# -*- coding: utf-8 -*-

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
hub.NOT_ERROR = (*hub.NOT_ERROR, falcon.http_status.HTTPStatus)


class FunctionExecutor(object):

    def __init__(self, http_wrapper=None, sentry_client=None, auth_func=None, log_exclude_fields=None, identity_func=None):
        self.http_wrapper = http_wrapper if http_wrapper else lambda d, s, m, c: d
        self.sentry_client = sentry_client
        self.auth_func = auth_func if auth_func else lambda req, func: True
        self.log_exclude_fields = log_exclude_fields if log_exclude_fields is not None else {}
        self.identity_func = identity_func

    def _http_wrapper(self, data=None, status=200, message='Success', code=0, response=None):
        if response:
            response.status = getattr(falcon, 'HTTP_{}'.format(status))
        return self.http_wrapper(data, status, message, code)

    def _process(self, func, args, kwargs, request, response):
        start_sig = blinker.signal('BeforeFunctionExecute')
        start_sig.send(request)

        if not self.auth_func(request, func):
            raise Unauthorized

        return self._http_wrapper(data=func(*args, **kwargs))

    def _send_sentry_exc(self, request):
        if self.sentry_client:
            if request:
                self.sentry_clinet.http_context({
                    'url': request.url,
                    'query_string': request.query_string,
                    'method': request.method,
                    'headers': request.headers,
                })
            self.sentry_client.captureException()

    def _prepare_log(self, func_name, args, kwargs, execution_time, request):
        if self.identity_func:
            kwargs['unique_identity'] = self.identity_func(request)
        kwargs_list = []
        for k, v in kwargs.items():
            if k not in self.ignore_fields:
                if isinstance(v, str):
                    v = "'{}'".format(v)
                kwargs_list.append('{}={}'.format(k, v))
        args_str = [str(a) for a in args] + kwargs_list
        return '{}({}) response {}ms'.format(
            func_name, ', '.join(args_str), execution_time)

    def _process_exception_output(self, e, func_logger, request, response):
        if self.http_wrapper:
            if isinstance(e, BasicUserException):
                return self._http_wrapper(
                    status=e.identity.http_code,
                    code=e.identity.code,
                    message=e.identity.error_msg,
                    response=response,
                )
            else:
                self._send_sentry_exc(request)
                func_logger.exception(e)
                return self._http_wrapper(
                    status=500,
                    code=0,
                    message='Internal Server Error',
                    response=response,
                )
        else:
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
                del kwargs['request']
            response = kwargs.get('response')
            if response:
                del kwargs['response']
            try:
                return self._process(func, args, kwargs, request, response)
            except falcon.http_status.HTTPStatus:
                raise
            except Exception as e:
                return self._process_exception_output(e, func_logger, request, response)
            finally:
                execution_time = (time.time() - start) * 1000
                self._finish_exec(execution_time, func_logger, args, kwargs, request, func)
        return wrapper
