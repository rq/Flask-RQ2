from datetime import datetime
from functools import wraps
from rq.decorators import job as rq_job
from rq.defaults import DEFAULT_RESULT_TTL
from rq.utils import backend_class
from flask import current_app


class job(rq_job):

    def __init__(self, queue_name='default', timeout=None,
                 result_ttl=DEFAULT_RESULT_TTL, ttl=None,
                 queue_class=None, depends_on=None, at_front=None, meta=None,
                 description=None):
        self.queue_name = queue_name
        self.queue_class = backend_class(self, 'queue_class',
                                         override=queue_class)
        self.timeout = timeout
        self.result_ttl = result_ttl
        self.ttl = ttl
        self.meta = meta
        self.depends_on = depends_on
        self.at_front = at_front
        self.description = description

    @property
    def connection(self):
        return self.rq2.connection

    @property
    def rq2(self):
        return current_app.extensions['rq2']

    @property
    def queue(self):
        return self.rq2.get_queue(self.queue_name)

    @property
    def scheduler(self):
        return self.rq2.get_scheduler()

    def __call__(self, f):
        @wraps(f)
        def enqueue(*args, **kwargs):
            timeout = kwargs.pop('timeout', self.timeout)
            result_ttl = kwargs.pop('result_ttl', self.result_ttl)
            ttl = kwargs.pop('ttl', self.ttl)
            return self.queue.enqueue_call(
                f, args=args, kwargs=kwargs, timeout=timeout,
                result_ttl=result_ttl, ttl=ttl,
                depends_on=self.depends_on, at_front=self.at_front,
                meta=self.meta, description=self.description,
            )

        @wraps(f)
        def enqueue_at(dt, *args, **kwargs):
            timeout = kwargs.pop('timeout', self.timeout)
            result_ttl = kwargs.pop('result_ttl', self.result_ttl)
            ttl = kwargs.pop('ttl', self.ttl)
            return self.scheduler.enqueue_at(
                dt, f, args=args, kwargs=kwargs, result_ttl=result_ttl,
                ttl=ttl, timeout=timeout, description=self.description,
                queue_name=self.queue_name,
            )

        @wraps(f)
        def enqueue_in(delta, *args, **kwargs):
            timeout = kwargs.pop('timeout', self.timeout)
            result_ttl = kwargs.pop('result_ttl', self.result_ttl)
            ttl = kwargs.pop('ttl', self.ttl)
            return self.scheduler.enqueue_in(
                delta, f, args=args, kwargs=kwargs, result_ttl=result_ttl,
                ttl=ttl, timeout=timeout, description=self.description,
                queue_name=self.queue_name,
            )

        @wraps(f)
        def schedule(scheduled_time=datetime.utcnow(), *args, **kwargs):
            repeat = kwargs.pop('repeat', None)
            interval = kwargs.pop('interval', None)
            timeout = kwargs.pop('timeout', self.timeout)
            result_ttl = kwargs.pop('result_ttl', self.result_ttl)
            ttl = kwargs.pop('ttl', self.ttl)
            return self.scheduler.schedule(
                scheduled_time, f, args=args, kwargs=kwargs, interval=interval,
                repeat=repeat, result_ttl=result_ttl, ttl=ttl,
                timeout=timeout, description=self.description,
                queue_name=self.queue_name,
            )

        @wraps(f)
        def cron(pattern, name, *args, **kwargs):
            repeat = kwargs.pop('repeat', None)
            timeout = kwargs.pop('timeout', self.timeout)
            return self.rq.get_scheduler().cron(
                pattern, f, args=args, kwargs=kwargs, repeat=repeat,
                queue_name=self.queue_name, id='cron-{}'.foramt(name),
                timeout=timeout, description=self.description,
            )

        f.enqueue = enqueue
        f.enqueue_at = enqueue_at
        f.enqueue_in = enqueue_in
        f.schedule = schedule
        f.cron = cron

        return f
