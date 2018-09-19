# -*- coding: utf-8 -*-
"""
    flask_rq2
    ~~~~~~~~~

    A Flask extension for RQ (Redis Queue).

    :copyright: (c) 2016 by Jannis Leidel.
    :license: MIT, see LICENSE for more details.
"""
from pkg_resources import get_distribution, DistributionNotFound

from .app import RQ  # noqa

__author__ = 'Jannis Leidel'

try:
    __version__ = get_distribution(__name__).version
except DistributionNotFound:
    # package is not installed
    pass
