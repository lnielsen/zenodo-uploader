# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
#
# Zenodo-Uploader is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, Unicode, \
    UnicodeText, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import UUIDType
from sqlalchemy_utils.functions import create_database, database_exists, \
    drop_database

# Define database, ORM and Session
engine = create_engine('sqlite:///log.db')
Model = declarative_base()
Session = sessionmaker(bind=engine)


class QueryMixin(object):
    """Mixing for adding query method."""

    @classmethod
    def query(cls):
        session = Session()
        q = session.query(cls)
        return q


class Deposit(Model, QueryMixin):
    """Log data from deposits."""

    __tablename__ = 'deposits'

    id = Column(Integer, primary_key=True)
    upload_id = Column(Unicode)
    done = Column(Boolean)
    etag = Column(Unicode)
    json = Column(UnicodeText)


class Error(Model, QueryMixin):
    """Log data from deposits."""

    __tablename__ = 'errors'

    id = Column(UUIDType, primary_key=True)
    upload_id = Column(Unicode)
    type = Column(Unicode)
    status_code = Column(Integer)
    body = Column(UnicodeText)


class RequestTiming(Model, QueryMixin):
    """Log time for each request."""

    __tablename__ = 'timing'

    id = Column(UUIDType, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    duration = Column(Integer)
    type = Column(Unicode)
    bytes = Column(Integer)


def recreate():
    """Drop and recreate database."""
    if database_exists(engine.url):
        drop_database(engine.url)
    create_database(engine.url)
    Model.metadata.create_all(engine)


def log_error(upload_id, rt, code, body):
    """Log request time."""
    session = Session()
    session.add(Error(
        id=uuid.uuid4(),
        upload_id=upload_id,
        type=rt,
        status_code=code,
        body=body,
    ))
    session.commit()


def log_time(t, upload_id=None, rt='', bytes=0):
    """Log request time."""
    session = Session()
    session.add(RequestTiming(
        id=uuid.uuid4(),
        duration=t,
        type=rt,
        bytes=bytes
    ))
    session.commit()


def log_deposit(r, upload_id):
    """Log deposit information."""
    session = Session()
    session.add(Deposit(
        id=r.json()['id'],
        upload_id=upload_id,
        done=False,
        etag=r.headers['etag'],
        json=r.text,
    ))
    session.commit()


def finish_deposit(id_):
    """Log deposit information."""
    session = Session()
    dep = session.query(Deposit).filter_by(id=id_).one()
    dep.done = True
    session.commit()
