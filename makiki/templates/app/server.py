# -*- coding: utf-8 -*-

from makiki.executor import FunctionExecutor
from makiki.http import generate_http_api

from .urls import user_apis


func_executor = FunctionExecutor()
api = generate_http_api(
    module_name=__name__,
    user_apis=user_apis,
    executor=func_executor,
)
