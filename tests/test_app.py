# -*- coding: utf-8 -*-
import types
from importlib import import_module

from redis import Redis
from rq.job import Job
from rq.queue import Queue
from rq.worker import Worker
from rq_scheduler import Scheduler

import pytest
from flask_rq2 import RQ


def exception_handler(*args, **kwargs):
    pass


def test_init_app(app, config):
    rq = RQ()
    assert 'rq2' not in getattr(app, 'extensions', {})
    assert getattr(rq, 'module', None) is None

    rq.init_app(app)
    assert rq.url == config.RQ_REDIS_URL
    assert isinstance(rq.connection, Redis)
    assert 'rq2' in getattr(app, 'extensions', {})
    assert rq.module_path == 'flask_rq2.backend_%s' % app.name


def test_rq_outside_flask():
    rq = RQ()
    # the redis connection is none since the Flask app context isn't there
    assert rq.connection is None


def test_config_redis(config, rq):
    assert rq.url == config.RQ_REDIS_URL
    assert isinstance(rq.connection, Redis)


def test_config_queues(config, rq):
    assert rq.queues == config.RQ_QUEUES


def test_config_async(app, config, rq):
    assert rq._async == config.RQ_ASYNC


def test_config_async_override(app, config, rq):
    rq2 = RQ(app, async=not config.RQ_ASYNC)
    assert rq2._async != config.RQ_ASYNC


def test_config_default_timeout(app, config):
    rq3 = RQ(app, default_timeout=911)
    assert rq3.default_timeout != Queue.DEFAULT_TIMEOUT
    assert rq3.default_timeout == 911


def test_config_scheduler_interval(config, rq):
    rq.scheduler_interval == config.RQ_SCHEDULER_INTERVAL


def test_config_scheduler_queue(config, rq):
    rq.scheduler_queue = config.RQ_SCHEDULER_QUEUE


def test_exception_handler(rq):
    rq.exception_handler(exception_handler)
    assert 'test_app.exception_handler' in rq._exception_handlers


def test_backend_init(app, rq):
    assert issubclass(rq.job_cls, Job)
    assert issubclass(rq.queue_cls, Queue)
    assert issubclass(rq.worker_cls, Worker)
    assert isinstance(rq.module, types.ModuleType)

    assert rq.queue_cls.job_class is rq.job_cls
    assert rq.worker_cls.queue_class is rq.queue_cls
    assert rq.worker_cls.job_class is rq.job_cls


def test_backend_module_importable(app, rq):
    assert rq.module_path == 'flask_rq2.backend_%s' % app.name
    assert rq.module == import_module(rq.module_path)


def test_get_worker(rq):
    worker = rq.get_worker()
    assert isinstance(worker, Worker)
    assert [queue.name for queue in worker.queues] == rq.queues


def test_get_worker_with_queues(rq):
    worker = rq.get_worker('some-queue')
    assert isinstance(worker, Worker)

    queue_names = [queue.name for queue in worker.queues]
    assert queue_names != rq.queues
    assert 'some-queue' in queue_names


def test_get_worker_with_exception_handlers(rq):
    rq.exception_handler(exception_handler)

    worker = rq.get_worker()
    assert exception_handler in worker._exc_handlers


def test_get_queue(rq):
    assert rq._queue_instances == {}
    queue = rq.get_queue()
    assert rq._queue_instances != {}
    assert queue in rq._queue_instances.values()

    assert isinstance(queue, Queue)
    assert isinstance(queue, rq.queue_cls)
    assert queue.name == rq.default_queue
    assert queue._default_timeout == rq.default_timeout
    assert queue._async == rq._async
    assert queue.connection == rq.connection


def test_get_queue_with_name(rq):
    queue = rq.get_queue('some-queue')
    assert queue.name == 'some-queue'
    assert queue.name in rq._queue_instances

    name2 = 'some-other-queue'
    assert name2 not in rq._queue_instances
    queue2 = rq.get_queue(name2)
    assert queue2.name == name2
    assert name2 in rq._queue_instances


def test_get_scheduler(rq):
    scheduler = rq.get_scheduler()

    assert isinstance(scheduler, Scheduler)
    assert isinstance(scheduler, rq.scheduler_cls)
    assert scheduler.queue_name == rq.scheduler_queue
    assert scheduler._interval == rq.scheduler_interval
    assert scheduler.connection == rq.connection


def test_get_scheduler_interval(rq):
    scheduler = rq.get_scheduler(23)
    assert scheduler._interval != rq.scheduler_interval
    assert scheduler._interval == 23


def test_get_scheduler_importerror(rq):
    rq.scheduler_cls = None  # in case scheduler can't be imported

    with pytest.raises(RuntimeError):
        rq.get_scheduler()
