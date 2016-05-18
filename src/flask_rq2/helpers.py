# -*- coding: utf-8 -*-
"""
    flask_rq2.helpers
    ~~~~~~~~~~~~~~~~~
"""
from datetime import datetime, timedelta


class JobFunctions(object):
    """
    Some helper functions that are addded to a function decorated
    with a :meth:`~flask_rq2.app.RQ.job` decorator.
    """
    #: the methods to add to jobs automatically
    functions = ['queue', 'schedule', 'cron']

    def __init__(self, rq, wrapped, queue_name, timeout,
                 result_ttl, ttl):
        self.rq = rq
        self.wrapped = wrapped
        self.queue_name = queue_name
        self.timeout = timeout
        self.result_ttl = result_ttl
        self.ttl = ttl

    def __repr__(self):
        full_name = '.'.join([self.wrapped.__module__, self.wrapped.__name__])
        return '<JobFunctions %s>' % full_name

    def queue(self, *args, **kwargs):
        """
        A function to queue a RQ job, e.g.::

            @rq.job
            def add(x, y):
                return x + y

            add.queue(1, 2)

        """
        depends_on = kwargs.pop('depends_on', None)
        at_front = kwargs.pop('at_front', False)
        description = kwargs.pop('description', None)
        job_id = kwargs.pop('job_id', None)
        return self.rq.get_queue(self.queue_name).enqueue_call(
            self.wrapped,
            args=args,
            kwargs=kwargs,
            timeout=self.timeout,
            result_ttl=self.result_ttl,
            ttl=self.ttl,
            description=description,
            depends_on=depends_on,
            job_id=job_id,
            at_front=at_front,
        )

    def schedule(self, time_or_delta, *args, **kwargs):
        """
        A function to schedule running a RQ job at a given time
        or after a given timespan::

            @rq.job
            def add(x, y):
                return x + y

            add.schedule(timedelta(hours=2), 1, 2)
            add.schedule(datetime(2016, 12, 31, 23, 59, 59), 1, 2)
            add.schedule(timedelta(days=14), 1, 2, repeat=1)

        """
        repeat = kwargs.pop('repeat', None)
        interval = kwargs.pop('interval', None)
        description = kwargs.pop('description', None)
        job_id = kwargs.pop('job_id', None)

        if isinstance(time_or_delta, timedelta):
            time = datetime.utcnow() + time_or_delta
        else:
            time = time_or_delta
        return self.rq.get_scheduler().schedule(
            time,
            self.wrapped,
            args=args,
            kwargs=kwargs,
            interval=interval,
            repeat=repeat,
            result_ttl=self.result_ttl,
            ttl=self.ttl,
            timeout=self.timeout,
            id=job_id,
            description=description,
            queue_name=self.queue_name,
        )

    def cron(self, pattern, name, *args, **kwargs):
        """
        A function to setup a RQ job as a cronjob::

            @rq.job
            def add(x, y):
                return x + y

            add.cron('* * * * *', 'add-some-numbers', 1, 2)

        """
        repeat = kwargs.pop('repeat', None)
        return self.rq.get_scheduler().cron(
            pattern,
            self.wrapped,
            args=args,
            kwargs=kwargs,
            repeat=repeat,
            queue_name=self.queue_name,
            id='cron-%s' % name,
        )
