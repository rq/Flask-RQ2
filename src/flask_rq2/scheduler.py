# -*- coding: utf-8 -*-
"""
    flask_rq2.scheduler
    ~~~~~~~~~~~~~~~~~~~

    The Flask application aware RQ scheduler class.

"""
from rq_scheduler.scheduler import Scheduler

from .job import FlaskJob


class FlaskScheduler(Scheduler):
    """
    The RQ Queue class that uses our Job class to
    be able to use Flask app context inside of jobs.
    """
    job_class = FlaskJob
