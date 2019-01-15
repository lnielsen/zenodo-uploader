# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
#
# Zenodo-Uploader is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import os
from os.path import basename
from time import time

import click
import requests
import sqlalchemy
from celery import Celery, chord
from celery.bin import worker

import config
import db
from utils2 import iter_uploads

# Create a Celery application
app = Celery('uploader')
app.config_from_object('celeryconfig')

# Create a requests session
client = requests.Session()
client.headers.update({
    'Authorization': 'Bearer {}'.format(config.ACCESS_TOKEN),
    'Accept': 'application/json',
})

# Definition of endpoints
endpoint = config.ENDPOINT


def raise_on_error(res, upload_id, rt):
    """Check response for errors."""
    if res.status_code not in [200, 201, 202]:
        db.log_error(upload_id, rt, res.status_code, res.text)
        raise Exception('[{}] {}'.format(
            res.status_code, res.text))


def timeit(params, f, *args, **kwargs):
    """Measure request time."""
    t1 = time()
    res = f(*args, **kwargs)
    t2 = time()
    raise_on_error(res, params['upload_id'], params['rt'])
    db.log_time(t2-t1, **params)
    return res


#
# Celery tasks (executed by worker)
#
@app.task
def create_deposit(upload_id, metadata, files):
    """Create a new deposit."""
    # Create deposit
    r = timeit(
        {'rt': 'create', 'upload_id': upload_id},
        client.post,
        endpoint,
        json={'metadata': metadata}
    )
    db.log_deposit(r, upload_id)

    # Log and extract parameters
    data = r.json()
    depid = data['id']
    bucket_url = data['links']['bucket']
    publish_url = data['links']['publish']

    # Execute file upload and publish tasks.
    chord(
        # File upload in parallel
        (upload_file.s(
            upload_id,
            '{}/{}'.format(bucket_url, name),
            f,
        ) for f, name in files),
        # Publish once all file upload have finished
        publish.s(depid, publish_url)
    )()


@app.task
def upload_file(upload_id, file_url, filepath):
    """Upload a file to a deposit."""
    size = os.stat(filepath).st_size
    with open(filepath, 'rb') as fp:
        r = timeit(
            {'rt': 'upload', 'bytes': size, 'upload_id': upload_id},
            client.put,
            file_url,
            data=fp,
            headers={
                'Content-Type': 'application/octet-stream'
            }
        )


@app.task
def publish(upload_id, depid, publish_url):
    """Publish the deposit."""
    r = timeit(
        {'rt': 'publish', 'upload_id': upload_id},
        client.post,
        publish_url
    )
    db.finish_deposit(depid)


#
# CLI commands
#

@click.group()
def cli():
    """Zenodo bulk uploader."""


@cli.command()
def init():
    """Initialize (or reset) database."""
    db.recreate()
    click.secho('Database created.', fg='green')


@cli.command()
@click.option('-n', '--dry-run', is_flag=True)
@click.argument('dir', nargs=-1, type=click.Path(
    exists=True, dir_okay=True, file_okay=False))
def process(dir, dry_run):
    """Process a bulk upload directory."""
    if dry_run:
        click.secho('Dry-run mode...', fg='yellow')
    i = 0
    for rootpath in dir:
        click.echo('Processing {}'.format(click.format_filename(rootpath)))
        for upload in iter_uploads(rootpath):
            if 'error' in upload:
                click.secho(
                    'ERROR ({}): {}'.format(
                        upload['path'], upload['error']),
                    fg='red'
                )
                continue
            if not dry_run:
                create_deposit.delay(
                    upload['id'], upload['metadata'], upload['files'])
            i += 1
    if dry_run:
        click.secho('Tested {} uploads.'.format(i), fg='green')
    else:
        click.secho('Sent {} uploads to the queue.'.format(i), fg='green')


@cli.command(name='worker')
def worker_cmd():
    """Start a Celery worker."""
    w = worker.worker(app=app)
    w.run(loglevel='INFO')


@cli.group()
def logs():
    """Inspect logging data."""
    pass


@logs.command()
def errors():
    """Inspect error logs."""
    click.echo('Upload ID;Request type;HTTP status code;Response body')
    for e in db.Error.query().all():
        click.echo('{upload_id};{type};{status};{body}'.format(
            upload_id=e.upload_id,
            type=e.type,
            status=e.status_code,
            body=e.body,
        ))


@logs.command()
@click.option('-u', '--unfinished', is_flag=True)
def deposits(unfinished):
    """Inspect error logs."""
    click.echo('Deposit ID,Upload ID,Done')
    q = db.Deposit.query()
    if unfinished:
        q = q.filter_by(done=False)
    for d in q.all():
        click.echo('{},{},{}'.format(d.id, d.upload_id, d.done))


@logs.command()
@click.option('-t', '--request-type', type=str)
def timing(request_type):
    """Inspect timing logs."""
    click.echo('Timestamp,Type,Time,Bytes')
    q = db.RequestTiming.query()
    if request_type:
        q = q.filter_by(type=request_type)

    for d in q.order_by('timestamp').all():
        click.echo('{},{},{},{}'.format(
            d.timestamp, d.type, d.duration, d.bytes))


if __name__ == '__main__':
    cli()
