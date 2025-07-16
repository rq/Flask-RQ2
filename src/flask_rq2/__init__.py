# -*- coding: utf-8 -*-
"""
    flask_rq2
    ~~~~~~~~~

    A Flask extension for RQ (Redis Queue).

    :copyright: (c) 2016 by Jannis Leidel.
    :license: MIT, see LICENSE for more details.
"""
from importlib.metadata import version, PackageNotFoundError

from .app import RQ  # noqa

def get_distribution(pkg_name):
    try:
        return version(pkg_name)
    except PackageNotFoundError:
        return None

__author__ = 'Jannis Leidel'

__version__ = get_distribution(__name__)

