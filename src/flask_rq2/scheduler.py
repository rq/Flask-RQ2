# -*- coding: utf-8 -*-
"""
    flask_rq2.scheduler
    ~~~~~~~~~~~~~~~~~~~

    The Flask application aware RQ scheduler class.

"""
from rq.scheduler import RQScheduler

from .job import FlaskJob


class FlaskScheduler(RQScheduler):
    """
    The RQ Queue class that uses our Job class to
    be able to use Flask app context inside of jobs.
    """
    job_class = FlaskJob
