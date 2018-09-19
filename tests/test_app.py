# -*- coding: utf-8 -*-
from redis import StrictRedis
from rq.queue import Queue
from rq.utils import import_attribute
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
    assert rq.redis_url == config.RQ_REDIS_URL
    assert isinstance(rq.connection, StrictRedis)
    assert 'rq2' in getattr(app, 'extensions', {})


def test_rq_outside_flask():
    rq = RQ()
    assert pytest.raises(RuntimeError, lambda: rq.connection)


def test_config_redis(config, rq):
    assert rq.redis_url == config.RQ_REDIS_URL
    assert isinstance(rq.connection, StrictRedis)


def test_config_queues(config, rq):
    assert rq.queues == config.RQ_QUEUES


def test_config_async(app, config, rq):
    assert rq._is_async == config.RQ_ASYNC


def test_config_async_override(app, config, rq):
    rq2 = RQ(app, is_async=not config.RQ_ASYNC)
    assert rq2._is_async != config.RQ_ASYNC


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
    assert isinstance(queue, import_attribute(rq.queue_class))
    assert queue.name == rq.default_queue
    assert queue._default_timeout == rq.default_timeout
    assert queue._is_async == rq._is_async
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
    assert isinstance(scheduler, import_attribute(rq.scheduler_class))
    assert scheduler.queue_name == rq.scheduler_queue
    assert scheduler._interval == rq.scheduler_interval
    assert scheduler.connection == rq.connection


def test_get_scheduler_interval(rq):
    scheduler = rq.get_scheduler(interval=23)
    assert scheduler._interval != rq.scheduler_interval
    assert scheduler._interval == 23


def test_get_scheduler_queue(rq):
    scheduler = rq.get_scheduler(queue='other')
    assert scheduler.queue_name == 'other'


def test_get_scheduler_importerror(rq):
    # in case scheduler can't be imported
    rq.scheduler_class = 'non.existing.Scheduler'

    with pytest.raises(ImportError):
        rq.get_scheduler()
