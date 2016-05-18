# -*- coding: utf-8 -*-
"""
    flask_rq2.app
    ~~~~~~~~~~~~~

    The core interface of Flask-RQ2.

"""
import sys
import types

import redis
from flask import _app_ctx_stack as stack
from rq.queue import Queue
from rq.utils import import_attribute
from rq.worker import DEFAULT_RESULT_TTL

try:
    from rq_scheduler import Scheduler
except ImportError:  # pragma: no cover
    Scheduler = None

try:
    import click
except ImportError:  # pragma: no cover
    click = None


class RQ(object):
    """
    The main RQ object to be used in user apps.
    """
    #: Name of the default queue.
    default_queue = 'default'

    #: The fallback default timeout value.
    default_timeout = Queue.DEFAULT_TIMEOUT

    #: The DSN (URL) of the Redis connection.
    url = 'redis://localhost:6379/0'

    #: List of queue names for RQ to work on.
    queues = [default_queue]

    #: Dotted import path to RQ Queue class to use as base class.
    queue_path = 'rq.queue.Queue'

    #: Dotted import path to RQ Workers class to use as base class.
    worker_path = 'rq.worker.Worker'

    #: Dotted import path to RQ Job class to use as base class.
    job_path = 'rq.job.Job'

    #: Name of RQ queue to schedule jobs in by rq-scheduler.
    scheduler_queue = default_queue

    #: Time in seconds the scheduler checks for scheduled jobs
    #: periodicically.
    scheduler_interval = 60

    #: The default job functions class.
    functions_path = 'flask_rq2.helpers.JobFunctions'

    def __init__(self, app=None, default_timeout=None, async=None):
        """
        Initialize the RQ interface.

        :param app: Flask application
        :type app: :class:`flask.Flask`
        :param default_timeout: The default timeout in seconds to use for jobs,
                                defaults to RQ's default of 180 seconds per job
        :type default_timeout: int
        :param async: Whether or not to run jobs asynchronously or in-process,
                      defaults to ``True``
        :type async: bool
        """
        if default_timeout is not None:
            self.default_timeout = default_timeout
        self._async = async
        self._jobs = []
        self._exception_handlers = []
        self._queue_instances = {}
        self._functions_cls = import_attribute(self.functions_path)

        if app is not None:
            self.init_app(app)

    @property
    def connection(self):
        ctx = stack.top
        if ctx is not None:
            if not hasattr(ctx, 'rq_redis'):
                ctx.rq_redis = self._connect()
            return ctx.rq_redis

    def _connect(self):
        return redis.from_url(self.url)

    def init_app(self, app):
        """
        Initialize the app, e.g. can be used if factory pattern is used.
        """
        self.url = app.config.setdefault(
            'RQ_REDIS_URL',
            self.url,
        )
        self.queues = app.config.setdefault(
            'RQ_QUEUES',
            self.queues,
        )
        self.queue_path = app.config.setdefault(
            'RQ_QUEUE_CLASS',
            self.queue_path,
        )
        self.worker_path = app.config.setdefault(
            'RQ_WORKER_CLASS',
            self.worker_path,
        )
        self.job_path = app.config.setdefault(
            'RQ_JOB_CLASS',
            self.job_path,
        )
        self.scheduler_queue = app.config.setdefault(
            'RQ_SCHEDULER_QUEUE',
            self.scheduler_queue,
        )
        self.scheduler_interval = app.config.setdefault(
            'RQ_SCHEDULER_INTERVAL',
            self.scheduler_interval,
        )

        #: Whether or not to run RQ jobs asynchronously or not,
        #: defaults to asynchronous
        _async = app.config.setdefault('RQ_ASYNC', True)
        if self._async is None:
            self._async = _async

        # register extension with app
        app.extensions = getattr(app, 'extensions', {})
        app.extensions['rq2'] = self

        # init the backends (job, queue and worker classes)
        self.init_backends(app)

        if hasattr(app, 'cli'):
            self.init_cli(app)

    def init_cli(self, app):
        """
        Initialize the Flask CLI support in case it was enabled for the
        app.

        Works with both Flask>=1.0's CLI support as well as the backport
        in the Flask-CLI package for Flask<1.0.
        """
        # in case click isn't installed after all
        if click is None:
            raise RuntimeError('Cannot import click. Is it installed?')
        # only add commands if we have a click context available
        from .cli import add_commands
        add_commands(app.cli, self)

    def init_backends(self, app):
        """
        Initialize the RQ backends with a closure so the RQ job class is
        aware of the Flask app context.
        """
        BaseJob = import_attribute(self.job_path)
        BaseQueue = import_attribute(self.queue_path)
        BaseWorker = import_attribute(self.worker_path)

        class AppJob(BaseJob):
            def perform(self):
                with app.app_context():
                    return super(AppJob, self).perform()

        class AppQueue(BaseQueue):
            job_class = AppJob

        class AppWorker(BaseWorker):
            queue_class = AppQueue
            job_class = AppJob

        self.job_cls = AppJob
        self.queue_cls = AppQueue
        self.worker_cls = AppWorker
        self.scheduler_cls = Scheduler

        self.module_path = 'flask_rq2.backend_%s' % app.name
        self.module = types.ModuleType(self.module_path)
        self.module.__path__ = []
        sys.modules[self.module_path] = self.module

        for backend_type in ['job', 'queue', 'worker']:
            backend_cls = getattr(self, '%s_cls' % backend_type)
            setattr(self.module, backend_cls.__name__, backend_cls)
            setattr(self, 'app_%s_path' % backend_type,
                    '%s.%s' % (self.module_path, backend_cls.__name__))

    def exception_handler(self, callback):
        """
        Decorator to add an exception handler to the worker, e.g.::

            rq = RQ()

            @rq.exception_handler
            def my_custom_handler(job, *exc_info):
                # do custom things here
                ...

        """
        path = '.'.join([callback.__module__, callback.__name__])
        self._exception_handlers.append(path)
        return callback

    def job(self, func_or_queue=None, timeout=None, result_ttl=None, ttl=None):
        """
        Decorator to mark functions for queuing via RQ, e.g.::

            rq = RQ()

            @rq.job
            def add(x, y):
                return x + y

        or::

            @rq.job(timeout=60, results_ttl=60*60)
            def add(x, y):
                return x + y

        Adds various helpers to the job function as documented in
        :class:`~flask_rq2.helpers.JobFunctions`.

        :param queue: Name of the queue to add job to, defaults to
                      :attr:`flask_rq2.app.RQ.default_queue`.
        :type queue: str
        :param timeout: The maximum runtime in seconds of the job before it's
                        considered 'lost', defaults to 180.
        :type timeout: int
        :param result_ttl: Time to persist the job results in Redis,
                           in seconds.
        :type timeout: int
        :param ttl: The maximum queued time of the job before it'll be
                    cancelled.
        :type timeout: int
        """
        if callable(func_or_queue):
            func = func_or_queue
            queue_name = self.default_queue
        else:
            func = None
            queue_name = func_or_queue

        def wrapper(wrapped):
            self._jobs.append(wrapped)
            helper = self._functions_cls(
                rq=self,
                wrapped=wrapped,
                queue_name=queue_name or self.default_queue,
                timeout=timeout or self.default_timeout,
                result_ttl=result_ttl or DEFAULT_RESULT_TTL,
                ttl=ttl,
            )
            wrapped.helper = helper
            for function in helper.functions:
                callback = getattr(helper, function, None)
                setattr(wrapped, function, callback)
            return wrapped

        if func is None:
            return wrapper
        else:
            return wrapper(func)

    def get_scheduler(self, interval=None):
        """
        When installed returns a ``rq_scheduler.Scheduler`` instance to
        schedule job execution, e.g.::

            scheduler = rq.get_scheduler(interval=10)

        :param interval: Time in seconds of the periodic check for scheduled
                         jobs.
        :type interval: int
        """
        if self.scheduler_cls is None:
            raise RuntimeError('Cannot import rq-scheduler. Is it installed?')
        if interval is None:
            interval = self.scheduler_interval
        return self.scheduler_cls(
            queue_name=self.scheduler_queue,
            interval=interval,
            connection=self.connection,
        )

    def get_queue(self, name=None):
        """
        Returns an RQ queue instance with the given name, e.g.::

            default_queue = rq.get_queue()
            low_queue = rq.get_queue('low')

        :param name: Name of the queue to return, defaults to
                     :attr:`~flask_rq2.RQ.default_queue`.
        :type name: str
        :return: An RQ queue instance.
        :rtype: ``rq.queue.Queue``
        """
        if name is None:
            name = self.default_queue
        queue = self._queue_instances.get(name)
        if queue is None:
            queue = self.queue_cls(
                name=name,
                default_timeout=self.default_timeout,
                async=self._async,
                connection=self.connection,
            )
            self._queue_instances[name] = queue
        return queue

    def get_worker(self, *queues):
        """
        Returns an RQ worker instance for the given queue names, e.g.::

            configured_worker = rq.get_worker()
            default_worker = rq.get_worker('default')
            default_low_worker = rq.get_worker('default', 'low')

        :param \*queues: Names of queues the worker should act on, falls back
                         to the configured queues.
        """
        if not queues:
            queues = self.queues
        queues = [self.get_queue(name) for name in queues]
        worker = self.worker_cls(queues, connection=self.connection)
        for exception_handler in self._exception_handlers:
            worker.push_exc_handler(import_attribute(exception_handler))
        return worker
