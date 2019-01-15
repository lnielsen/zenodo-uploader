# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
#
# Zenodo-Uploader is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

import os

ACCESS_TOKEN = 'CHANGEME'
"""Zenodo API access token."""

ENDPOINT = 'https://sandbox.zenodo.org/api/deposit/depositions'
"""Zenodo API endpoint"""


FILES_PATH_TEMPLATES = [
    ('testupload2/img-arch/{barcode}/barcode.jpg', '{barcode}.jpg'),
]
"""List of templates for filename generation.

Each entry in the list has too look like this:

    ('<path template>', '<name template>'),

You can use the following variables in the templates:

- barcode
- name
- family
- basename (only in name template)
"""
