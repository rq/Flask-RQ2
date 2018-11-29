# -*- coding: utf-8 -*-
"""
    flask_rq2.functions
    ~~~~~~~~~~~~~~~~~~~
"""
from datetime import datetime, timedelta


class JobFunctions(object):
    """
    Some helper functions that are added to a function decorated
    with a :meth:`~flask_rq2.app.RQ.job` decorator.
    """
    #: the methods to add to jobs automatically
    functions = ['queue', 'schedule', 'cron']

    def __init__(self, rq, wrapped, queue_name, timeout, result_ttl, ttl,
                 depends_on, at_front, meta, description):
        self.rq = rq
        self.wrapped = wrapped
        self._queue_name = queue_name
        self._timeout = timeout
        self._result_ttl = result_ttl
        # job TTLs don't have a default value
        # https://github.com/nvie/rq/issues/873
        self.ttl = ttl
        self._depends_on = depends_on
        self._at_front = at_front
        self._meta = meta
        self._description = description

    def __repr__(self):
        full_name = '.'.join([self.wrapped.__module__, self.wrapped.__name__])
        return '<JobFunctions %s>' % full_name

    @property
    def queue_name(self):
        # Catch empty strings and None
        return self._queue_name or self.rq.default_queue

    @queue_name.setter
    def queue_name(self, value):
        self._queue_name = value

    @property
    def timeout(self):
        return self._timeout or self.rq.default_timeout

    @timeout.setter
    def timeout(self, value):
        self._timeout = value

    @property
    def result_ttl(self):
        # Allow a result TTL of 0
        if self._result_ttl is None:
            return self.rq.default_result_ttl
        else:
            return self._result_ttl

    @result_ttl.setter
    def result_ttl(self, value):
        self._result_ttl = value

    def queue(self, *args, **kwargs):
        """
        A function to queue a RQ job, e.g.::

            @rq.job(timeout=60)
            def add(x, y):
                return x + y

            add.queue(1, 2, timeout=30)

        :param \\*args: The positional arguments to pass to the queued job.

        :param \\*\\*kwargs: The keyword arguments to pass to the queued job.

        :param queue: Name of the queue to queue in, defaults to
                      queue of of job or :attr:`~flask_rq2.RQ.default_queue`.
        :type queue: str

        :param timeout: The job timeout in seconds.
                        If not provided uses the job's timeout or
                        :attr:`~flask_rq2.RQ.default_timeout`.
        :type timeout: int

        :param description: Description of the job.
        :type description: str

        :param result_ttl: The result TTL in seconds. If not provided
                           uses the job's result TTL or
                           :attr:`~flask_rq2.RQ.default_result_ttl`.
        :type result_ttl: int

        :param ttl: The job TTL in seconds. If not provided
                    uses the job's TTL or no TTL at all.
        :type ttl: int

        :param depends_on: A job instance or id that the new job depends on.
        :type depends_on: ~flask_rq2.job.FlaskJob or str

        :param job_id: A custom ID for the new job. Defaults to an
                       :mod:`UUID <uuid>`.
        :type job_id: str

        :param at_front: Whether or not the job is queued in front of all other
                         enqueued jobs.
        :type at_front: bool

        :param meta: Additional meta data about the job.
        :type meta: dict

        :return: An RQ job instance.
        :rtype: ~flask_rq2.job.FlaskJob
        """
        queue_name = kwargs.pop('queue', self.queue_name)

        timeout = kwargs.pop('timeout', self.timeout)
        result_ttl = kwargs.pop('result_ttl', self.result_ttl)
        ttl = kwargs.pop('ttl', self.ttl)
        depends_on = kwargs.pop('depends_on', self._depends_on)
        job_id = kwargs.pop('job_id', None)
        at_front = kwargs.pop('at_front', self._at_front)
        meta = kwargs.pop('meta', self._meta)
        description = kwargs.pop('description', self._description)
        return self.rq.get_queue(queue_name).enqueue_call(
            self.wrapped,
            args=args,
            kwargs=kwargs,
            timeout=timeout,
            result_ttl=result_ttl,
            ttl=ttl,
            depends_on=depends_on,
            job_id=job_id,
            at_front=at_front,
            meta=meta,
            description=description,
        )

    def schedule(self, time_or_delta, *args, **kwargs):
        """
        A function to schedule running a RQ job at a given time
        or after a given timespan::

            @rq.job
            def add(x, y):
                return x + y

            add.schedule(timedelta(hours=2), 1, 2, timeout=10)
            add.schedule(datetime(2016, 12, 31, 23, 59, 59), 1, 2)
            add.schedule(timedelta(days=14), 1, 2, repeat=1)

        :param \\*args: The positional arguments to pass to the queued job.

        :param \\*\\*kwargs: The keyword arguments to pass to the queued job.

        :param queue: Name of the queue to queue in, defaults to
                      queue of of job or :attr:`~flask_rq2.RQ.default_queue`.
        :type queue: str

        :param timeout: The job timeout in seconds.
                        If not provided uses the job's timeout or
                        :attr:`~flask_rq2.RQ.default_timeout`.
        :type timeout: int

        :param description: Description of the job.
        :type description: str

        :param result_ttl: The result TTL in seconds. If not provided
                           uses the job's result TTL or
                           :attr:`~flask_rq2.RQ.default_result_ttl`.
        :type result_ttl: int

        :param ttl: The job TTL in seconds. If not provided
                    uses the job's TTL or no TTL at all.
        :type ttl: int

        :param repeat: The number of times the job needs to be repeatedly
                       queued. Requires setting the ``interval`` parameter.
        :type repeat: int

        :param interval: The interval of repetition as defined by the
                         ``repeat`` parameter in seconds.
        :type interval: int

        :param job_id: A custom ID for the new job. Defaults to a UUID.
        :type job_id: str

        :return: An RQ job instance.
        :rtype: ~flask_rq2.job.FlaskJob

        """
        queue_name = kwargs.pop('queue', self.queue_name)
        timeout = kwargs.pop('timeout', self.timeout)
        description = kwargs.pop('description', None)
        result_ttl = kwargs.pop('result_ttl', self.result_ttl)
        ttl = kwargs.pop('ttl', self.ttl)
        repeat = kwargs.pop('repeat', None)
        interval = kwargs.pop('interval', None)
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
            result_ttl=result_ttl,
            ttl=ttl,
            timeout=timeout,
            id=job_id,
            description=description,
            queue_name=queue_name,
        )

    def cron(self, pattern, name, *args, **kwargs):
        """
        A function to setup a RQ job as a cronjob::

            @rq.job('low', timeout=60)
            def add(x, y):
                return x + y

            add.cron('* * * * *', 'add-some-numbers', 1, 2, timeout=10)

        :param \\*args: The positional arguments to pass to the queued job.

        :param \\*\\*kwargs: The keyword arguments to pass to the queued job.

        :param pattern: A Crontab pattern.
        :type pattern: str

        :param name: The name of the cronjob.
        :type name: str

        :param queue: Name of the queue to queue in, defaults to
                      queue of of job or :attr:`~flask_rq2.RQ.default_queue`.
        :type queue: str

        :param timeout: The job timeout in seconds.
                        If not provided uses the job's timeout or
                        :attr:`~flask_rq2.RQ.default_timeout`.
        :type timeout: int

        :param description: Description of the job.
        :type description: str

        :param repeat: The number of times the job needs to be repeatedly
                       queued via the cronjob. Take care only using this for
                       cronjob that don't already repeat themselves natively
                       due to their crontab.
        :type repeat: int

        :return: An RQ job instance.
        :rtype: ~flask_rq2.job.FlaskJob

        """
        queue_name = kwargs.pop('queue', self.queue_name)
        timeout = kwargs.pop('timeout', self.timeout)
        description = kwargs.pop('description', None)
        repeat = kwargs.pop('repeat', None)
        return self.rq.get_scheduler().cron(
            pattern,
            self.wrapped,
            args=args,
            kwargs=kwargs,
            repeat=repeat,
            queue_name=queue_name,
            id='cron-%s' % name,
            timeout=timeout,
            description=description,
        )
