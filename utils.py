# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
#
# Zenodo-Uploader is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import json
import os
from os.path import basename, exists, join


def iter_uploads(path):
    """Iterate uploads in a direcotry."""
    with os.scandir(path) as it:
        for entry in it:
            if not entry.name.startswith('.') and entry.is_dir():
                yield make_upload(entry.path)


def make_upload(path):
    """Make an upload from a directory."""
    metadatafile = join(path, 'metadata.json')
    if not os.path.exists(metadatafile):
        return {'error': 'No metadata.json file.', 'path': path}
    try:
        with open(metadatafile) as fp:
            metadata = json.load(fp)
    except Exception:
        return {'error': 'Could not read/parse metadata.json.', 'path': path}

    files = []
    with os.scandir(path) as it:
        for entry in it:
            if not entry.name.startswith('.') \
                    and entry.name != 'metadata.json'\
                    and entry.is_file():
                files.append((entry.path, entry.name))

    if len(files) == 0:
        return {'error': 'Missing files.', 'path': path}

    return {
        'metadata': metadata,
        'files': files,
        'path': path,
        'id': basename(path),
    }
