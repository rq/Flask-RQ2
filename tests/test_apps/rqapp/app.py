from __future__ import absolute_import, print_function

from flask import Flask
from flask_rq2 import RQ


class Config(object):
    RQ_REDIS_URL = 'redis://localhost:6379/15'
    RQ_QUEUES = ['test-queue']
    RQ_ASYNC = False
    RQ_SCHEDULER_QUEUE = 'scheduler-queue'
    RQ_SCHEDULER_INTERVAL = 42


testapp = Flask('testapp')
testapp.config.from_object(Config())
testrq = RQ(testapp)
