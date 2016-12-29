# -*- coding: utf-8 -*-

import functools
import logging
import random

from contextlib import contextmanager
from threading import local

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy.orm import (
    Session as _Session,
    scoped_session,
    sessionmaker,
)

logger = logging.getLogger(__name__)
db_ctx = local()


def gen_commit_deco(DBSession):
    def wrap(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            register_db_commit = getattr(db_ctx, 'register_db_commit', False)
            if not register_db_commit:
                db_ctx.register_db_commit = True
            result = func(*args, **kwargs)
            if not register_db_commit:
                try:
                    DBSession().flush()
                    DBSession().commit()
                except SQLAlchemyError:
                    DBSession().rollback()
                    raise
                finally:
                    DBSession().close()
                    delattr(db_ctx, 'register_db_commit')
            return result
        return wrapper
    return wrap


def make_pg_engine(db_conn_config, pool_size=5, max_overflow=0, pool_recycle=1200, client_encoding='utf-8', echo=False, logging_name='default'):
    DEFAULT_URL = ("postgresql+psycopg2://{user}:{password}"
                   "@{host}:{port}/{database}")
    dsn = DEFAULT_URL.format(**db_conn_config)
    return create_engine(
        dsn, pool_size=pool_size, max_overflow=max_overflow,
        pool_recycle=pool_recycle,
        client_encoding=client_encoding,
        echo=echo,
        logging_name=logging_name,
    )


def make_session(master_engine, slave_engines=None):
    class Session(_Session):
        _force_master = False

        def get_bind(self, mapper=None, clause=None):
            if self._force_master or self._flushing or not slave_engines:
                return master_engine
            else:
                return random.choice(slave_engines)

        @contextmanager
        def using_master(self):
            try:
                self._force_master = True
                yield self
            finally:
                self._force_master = False

    return scoped_session(
        sessionmaker(
            class_=Session,
            expire_on_commit=False,
            autoflush=False,
        )
    )
