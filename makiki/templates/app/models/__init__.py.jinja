# -*- coding: utf-8 -*-

import blinker

from sqlalchemy.ext.declarative import declarative_base

from ..config import DATABASE_CONFIG

from makiki.database import (
    make_pg_engine,
    make_session,
    gen_commit_deco,
)


engine = make_pg_engine(DATABASE_CONFIG)
DBSession = make_session(engine)
db_commit = gen_commit_deco(DBSession)
DeclarativeBase = declarative_base()


def remove_session(sender):
    if DBSession().new or DBSession().dirty or DBSession().deleted:
        DBSession().rollback()
    DBSession.remove()


blinker.signal('AfterFunctionExecute').connect(remove_session)
