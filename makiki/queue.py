# -*- coding: utf-8 -*-

import uuid
import importlib
import logging
import time
import functools

from threading import local

try:
    from celery import (
        Celery,
        signals,
    )
except ImportError:
    raise ImportError('To use queue module, you must install celery.')
try:
    from sqlalchemy import event
except:
    event = None

logger = logging.getLogger(__name__)
async_ctx = local()


class NestorAsyncTask(object):
    __slots__ = (
        'task_id', 'module_name', 'func_name', 'args', 'kwargs',
        'countdown', 'send_after_commit', 'extra_celery_kwargs', 'apply_queue',
    )

    def __init__(
            self, module_name, func_name, args=None, kwargs=None,
            countdown=0, send_after_commit=False,
            apply_queue='wedding_queue', extra_celery_kwargs=None,
    ):
        mod = importlib.import_module(module_name)
        if not hasattr(mod, func_name):
            raise ValueError('Invalid API Endpoint is provided.')
        self.task_id = uuid.uuid1().hex
        self.module_name = module_name
        self.func_name = func_name
        self.args = args if args is not None else ()
        self.kwargs = kwargs if kwargs is not None else {}
        self.countdown = countdown if countdown >= 0 else 0
        self.send_after_commit = bool(send_after_commit)
        self.extra_celery_kwargs = extra_celery_kwargs if extra_celery_kwargs is not None else {}
        self.apply_queue = apply_queue

    def register(self):
        if self.send_after_commit:
            if hasattr(async_ctx, 'reged_tasks'):
                async_ctx.reged_tasks.add(self)
            else:
                async_ctx.reged_tasks = {self}
        else:
            raise ValueError('Cannot register task without send_after_commit flag.')

    def send(self, async_api):
        return async_api.si(
            self.module_name, self.func_name,
            *self.args, nestor_task_id=self.task_id, **self.kwargs
        ).apply_async(
            countdown=self.countdown,
            queue=self.apply_queue,
            **self.extra_celery_kwargs
        )


def send_after_commit_tasks(session):
    if not hasattr(async_ctx, 'reged_tasks'):
        return
    for task in async_ctx.reged_tasks:
        task.send()
    delattr(async_ctx, 'reged_tasks')


def make_send_task(async_api):
    return functools.partial(send_task, async_api=async_api)


def send_task(async_api, module_name, api_name, *args, countdown=0, send_after_commit=False, extra_celery_kwargs=None, **kwargs):
    task = NestorAsyncTask(
        module_name=module_name,
        func_name=api_name,
        args=args,
        kwargs=kwargs,
        countdown=countdown,
        send_after_commit=send_after_commit,
        extra_celery_kwargs=extra_celery_kwargs,
    )
    if send_after_commit:
        task.register()
    else:
        task.send(async_api)
    return task.task_id


def register_to_celery(celery_broker, celery_config, func_executor, retry_wait=5, max_retries=12, DBSession=None):

    def async_task(self, module_name, api_name, *args, nestor_task_id=None, **kwargs):
        try:
            mod = importlib.import_module(module_name)
            func = getattr(mod, api_name)
            return func_executor(func)(*args, **kwargs)
        except Exception as e:
            self.retry(exc=e, countdown=retry_wait)

    broker = 'amqp://{user}:{password}@{host}:{port}/{vhost}'.\
        format(**celery_broker)

    celery_app = Celery(broker=broker)
    celery_app.conf.update(**celery_config)

    async_api = celery_app.task(max_retries=max_retries, bind=True)(async_task)
    signals.setup_logging.connect(init_celery_log)
    if DBSession:
        if event:
            event.listens_for(DBSession, 'after_commit')(send_after_commit_tasks)
        else:
            raise ImportError('You must install sqlalchemy first.')

    return async_api


def init_celery_log(loglevel=logging.INFO, **kwargs):
    handler = logging.StreamHandler()
    formatter = logging.Formatter('%(asctime)s [%(process)d] [%(levelname)s] %(name)s: %(message)s')
    handler.setFormatter(formatter)
    log = logging.getLogger('')
    log.addHandler(handler)
    log.setLevel(loglevel)
    return log
