# Zenodo Uploader

Zenodo Uploader is a small application to efficiently upload large number of
records and files to Zenodo via the Deposit API.

If you plan to make large uploads to Zenodo, please get in touch with us
before hand at https://zenodo.org/support

## Prerequisites

- Docker and Docker-Compose
- Python 3
- virtulaenv-wrapper (for the ``mkvirtualenv`` command)

## Install

```console
$ git clone https://github.com/lnielsen/zenodo-uploader.git
$ cd zenodo-uploader
$ mkvirutalenv uploader
(uploader)$ pip install -r requirements.txt
```

## Configure

You must edit ``config.py``:

```python
ACCESS_TOKEN = '...'
ENDPOINT = 'https://sandbox.zenodo.org/api/deposit/depositions'
```

## Run

Start the RabbitMQ message broker (required by the worker):

```console
$ docker-compose up -d
```

Note that the message broker have an admin interface you can see on
http://localhost:15672 (login with guest/guest).

Initialize (or reset) the log database:

```console
(uploader)$ python app.py init
```

This will create a SQLite3 database in the current working directory called
``log.db``.

Finally start the Celery worker:

```console
(uploader)$ python app.py worker
```

Note, if you make changes to the code, you'll have to restart the worker for
the code changes to be picked up.

## Usage

#### Dry-run

Process bulk upload (in dry-run mode which checks the local data):

```console
(uploader)$ python app.py process -n testupload2/csvdir/
```

This will expect to find a directory with CSV files. Each CSV file is read,
and each row is converted into an upload to Zenodo. See ``utils2.py`` for
details on how these uploads are generated from the CSV (e.g. to fix metadata).

You'll need to configure the ``FILES_PATH_TEMPLATES`` in ``config.py``. This
option configures where to look for files for each upload.

#### Process

Process bulk upload (for real)

```console
(uploader)$ python app.py process testupload2/csvdir/
```

You should now see the worker processing tasks.

#### Inspecting the logs

List all deposits:

```console
(uploader)$ python app.py logs deposits
Deposit ID,Upload ID,Done
256643,testlin#BR0000010599976,True
```

List errors:

```console
(uploader)$ python app.py logs errors
testlin#BR0000010599976;create;400;{"status": 400, "message": "Validation error.", "errors": [{"field": "metadata.communities", "message": "Invalid communities: belgiumherbarium"}]}
```

List request performance:

```console
(uploader)$  python app.py logs timing
Type,Time,Bytes
Timestamp,Type,Time,Bytes
2019-01-18 16:14:03.193291,create,0.5013158321380615,0
2019-01-18 16:14:07.530581,upload,4.285969257354736,3692386
2019-01-18 16:14:08.946722,publish,1.360076904296875,0
```

List request performance (filter by type):

```console
(uploader)$ python app.py logs timing -t upload
Type,Time,Bytes
upload,0.4276392459869385,3692386
```

You can reset the database at any point by running:

```console
(uploader)$ python app.py init
```

## Querying the log database

If you need more advanced querying of the database, you can simply open it in
SQLite3:

```console
$ sqlite3 log.db
SQLite version 3.24.0 2018-06-04 14:10:15
Enter ".help" for usage hints.
sqlite>
```
