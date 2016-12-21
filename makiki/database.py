# -*- coding: utf-8 -*-

import functools
import logging

from threading import local

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError

from sqlalchemy.orm import (
    Session,
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


def make_pg_engine(db_conn_config, pool_size=5, max_overflow=0, pool_recycle=1200, client_encoding='utf-8'):
    DEFAULT_URL = ("postgresql+psycopg2://{user}:{password}"
                   "@{host}:{port}/{database}")
    dsn = DEFAULT_URL.format(**db_conn_config)
    return create_engine(
        dsn, pool_size=pool_size, max_overflow=max_overflow,
        pool_recycle=pool_recycle,
        client_encoding=client_encoding,
    )


def make_session(engine):
    return scoped_session(
        sessionmaker(
            class_=Session,
            expire_on_commit=False,
            autoflush=False,
            bind=engine,
        )
    )
