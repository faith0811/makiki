# -*- coding: utf-8 -*-

import subprocess
import os
import argparse
from contextlib import suppress
from jinja2 import Template
from gunicorn.app.base import BaseApplication


def init(args):
    print('Gathering information for initial...')
    app_name = input('App name: ')
    author_name = input('Author name: ')
    default_app_addr = 'https://github.com/{author_name}/{app_name}'.format(author_name=author_name, app_name=app_name)
    app_addr = input('App Home address (default: {addr}): '.format(addr=default_app_addr)) or default_app_addr
    database_addr = input('Database address (default: localhost)') or 'localhost'
    database_port = input('Database port (default: 5432)') or 5432
    database_user = input('Database user (default: postgres)') or 'postgres'
    database_password = input('Database password (default: postgres)') or 'postgres'
    database_db = input('Database dbname (default: postgres)') or 'postgres'

    package_infos = locals()
    # TODO: render infos into template and generate static python files.

    template_path = os.path.join(os.path.dirname(__file__), 'templates')
    for current_dir, _, files in os.walk(template_path):
        target_dir = os.path.relpath(current_dir, template_path)
        with suppress(FileExistsError, IsADirectoryError):
            os.mkdir(target_dir)

        for file_ in files:
            with open(os.path.join(current_dir, file_), 'r') as f:
                content = f.read()
            rendered = Template(content).render(**package_infos)
            with open(os.path.join(target_dir, file_.rstrip('.jinja')), 'w') as f:
                f.write(rendered)
    os.rename('app', app_name)
    subprocess.call(['python', 'setup.py', 'develop'])


def dev_run(args):
    try:
        from gunicorn_config import import_wsgi
    except ImportError:
        raise ImportError('Must run inside a Makiki app and keep gunicorn_config file untouched.')

    class DevServer(BaseApplication):
        def __init__(self, bind, workers):
            self._bind = bind
            self._workers = workers
            super().__init__()

        def load_config(self):
            self.cfg.set('bind', self._bind)
            self.cfg.set('workers', self._workers)
            self.cfg.set('worker_class', 'gevent')
            self.cfg.set('reload', True)

        def load(self):
            return import_wsgi()

    DevServer(args.bind, args.workers).run()


def main_parser():
    root_parser = argparse.ArgumentParser()
    sub_parsers = root_parser.add_subparsers()
    sub_parsers.required = True
    sub_parsers.dest = 'command'

    init_parser = sub_parsers.add_parser('init')
    init_parser.set_defaults(func=init)

    dev_run_parser = sub_parsers.add_parser('dev-run')
    dev_run_parser.add_argument('--bind', default='0.0.0.0:8000', help='default: 0.0.0.0:8000')
    dev_run_parser.add_argument('--workers', default=1, help='default: 1')
    dev_run_parser.set_defaults(func=dev_run)

    args = root_parser.parse_args()
    args.func(args)
