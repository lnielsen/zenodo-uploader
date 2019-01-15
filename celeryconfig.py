# -*- coding: utf-8 -*-
#
# Copyright (C) 2019 CERN.
#
# Zenodo-Uploader is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

broker_url = 'pyamqp://guest@localhost//'
result_backend = 'redis://localhost/0'
task_serializer = 'msgpack'
result_serializer = 'msgpack'
accept_content = ['msgpack']

task_annotations = {
    'app.upload': {'rate_limit': '1000/m'}
}
