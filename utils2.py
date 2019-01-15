# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
#
# Zenodo-Uploader is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import csv
import json
import os
from os.path import basename, dirname, exists, isfile, join

import config


def iter_uploads(path):
    """Iterate CSV files in a direcotry."""
    with os.scandir(path) as it:
        for entry in it:
            if not entry.name.startswith('.') and entry.is_file():
                for row in iter_csv(entry.path):
                    yield make_upload(entry.path, row)


def iter_csv(path):
    """Iterate over rows in a CSV file."""
    with open(path) as fp:
        reader = csv.reader(fp, delimiter=',', quotechar='"')
        for row in reader:
            yield {'barcode': row[0], 'name': row[1], 'family': row[2]}


def make_upload(path, row):
    """Make an upload from a row in CSV file."""
    metadata = {
        'upload_type': 'image',
        'image_type': 'photo',
        'title': '{name} ({barcode})'.format(**row),
        'creators': [{'name': 'Meise Botanic Garden'}],
        'description': (
            'Belgium Herbarium image of <a href="https://www.plantentuin'
            'meise.be">Meise Botanic Garden</a>.'),
        'access_right': 'open',
        'license': 'CC-BY-SA-4.0',
        # 'communities': [{'identifier': 'belgiumherbarium'}],
        'grants': [{'id': '777483'}],
        'related_identifiers': [{
            'identifier': 'http://www.botanicalcollections.be/'
                          'specimen/{barcode}'.format(**row),
            'relation': 'isAlternateIdentifier',
        }],
        'keywords': [
            'Biodiversity',
            'Taxonomy',
            'Terrestrial',
            'Herbarium',
            row['family'],
        ],
        'imprint_publisher': 'Meise Botanic Garden Herbarium'
    }

    # Find files for this upload
    files = []
    for path_tpl, name_tpl in config.FILES_PATH_TEMPLATES:
        # Render each template into a a) full path on disk and b) name of file
        # on Zenodo.
        fpath = path_tpl.format(**row)
        name = name_tpl.format(basename=basename(fpath), **row)
        # Check if the file exists, and if so add it to the list of files
        # to upload.
        if exists(fpath) and isfile(fpath):
            files.append((fpath, name))

    if len(files) == 0:
        return {'error': 'Missing files.', 'path': path + '#' + row['barcode']}

    return {
        'metadata': metadata,
        'files': files,
        'path': path,
        'id': '{basename}#{barcode}'.format(basename=basename(path), **row),
    }
