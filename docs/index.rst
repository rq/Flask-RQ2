Flask-RQ2
=========

.. include:: ../README.rst
   :start-after: .. snip
   :end-before: .. snap

Decorators
----------

``@job``
~~~~~~~~

A decorator to mark a function as an `RQ job`_ and to add some helpers to
the function to simplify enqueuing:

.. code-block:: python

    from flask_rq2 import RQ

    rq = RQ()

    @rq.job
    def add(x, y):
        return x + y

Then in your app code:

.. code-block:: python

    job = add.queue(1, 2)

A specific queue name can also be passed as argument:

.. code-block:: python

    @rq.job('low', timeout=60)
    def add(x, y):
        return x + y

Or if you decide to use a different queue and timeout
dynamically during runtime:

.. code-block:: python

    job2 = add.queue(3, 4, queue='high', timeout=60 * 2)

.. versionchanged:: 17.2

    The ``queue`` job function now takes a few more parameters.
    See the full `API docs`_ for more information.

Some other parameters are available as well:

.. code-block:: python

    @rq.job('low', timeout=180, result_ttl=60 * 60, ttl=60 * 60 * 24)
    def add(x, y):
        return x + y

You can additionally schedule jobs to run at a certain time, after a certain
timespan or by a cron-like plan:

.. code-block:: python

    @rq.job
    def add(x, y):
        return x + y

    # queue job in 60 seconds
    add.schedule(timedelta(seconds=60), 1, 2)

    # queue job at a certain datetime (UTC!)
    add.schedule(datetime(2016, 12, 31, 23, 59, 59), 1, 2)

    # queue job in 14 days and then repeat once 14 days later
    add.schedule(timedelta(days=14), 1, 2, repeat=1)

    # queue job in 12 hours with a different queue
    add.schedule(timedelta(hours=12), 1, 2, queue='high', timeout=60 * 2)

    # queue job every day at noon (UTC!)
    add.cron('0 0 12 * * ?', 'add-one-two', 1, 2)

    # queue job every minute with a different queue
    add.cron('* * * * *', 'add-one-two', 1, 2, queue='high', timeout=55)

.. versionchanged:: 17.2

    The ``schedule`` and ``cron`` functions now take a few more parameters.
    See the full `API docs`_ for more information.

See the full `API docs`_ for more information about the job functions.

.. _`API docs`: http://flask-rq2.readthedocs.io/en/stable/api/
.. _`RQ job`: http://python-rq.org/docs/jobs/

``@exception_handler``
~~~~~~~~~~~~~~~~~~~~~~

An optional decorator for `custom exception handlers`_ that the RQ worker
should call when catching exceptions during job execution.

.. code-block:: python

    from flask_rq2 import RQ

    rq = RQ()

    @rq.exception_handler
    def send_alert_to_ops(job, *exc_info):
        # call other code to send alert to OPs team

The exception handler will automatically be used when running the worker
from the ``get_worker`` method or the CLI integration.

.. _`custom exception handlers`: http://python-rq.org/docs/exceptions/

RQ backends
-----------

There are a few useful methods to fetch RQ backend objects for advanced
patterns.

They will use the same Flask config values as the decorators and CLI
integration and should be used instead of rq's own functions with
the same name.

``get_queue``
~~~~~~~~~~~~~

Returns default queue or specific queue for name given as argument:

.. code-block:: python

    from flask_rq2 import RQ

    rq = RQ()

    default_queue = rq.get_queue()
    low_queue = rq.get_queue('low')

    easy_job = default_queue.enqueue(add, args=(1, 2))
    hard_job = low_queue.enqueue(add, args=(1e100, 2e200))

``get_worker``
~~~~~~~~~~~~~~

Returns a worker for default queue or specific queues for names given as arguments:

.. code-block:: python

    from flask_rq2 import RQ

    rq = RQ()

    # Creates a worker that handle jobs in ``default`` queue.
    default_worker = rq.get_worker()
    default_worker.work(burst=True)

    # Creates a worker that handle jobs in both ``simple`` and ``low`` queues.
    low_n_simple_worker = rq.get_worker('low', 'simple')
    low_n_simple_worker.work(burst=True)

``get_scheduler``
~~~~~~~~~~~~~~~~~

Returns an `RQ Scheduler`_ instance for periodically enqueuing jobs:

.. code-block:: python

    from flask_rq2 import RQ

    rq = RQ()

    # check every 10 seconds if there are any jobs to enqueue
    scheduler = rq.get_scheduler(interval=10)
    scheduler.run()

.. versionchanged:: 17.2

    The ``get_scheduler`` method now takes an optional ``queue`` parameter
    to override the default scheduler queue.

CLI support
-----------

Flask-RQ2 only supports the Click_ based `CLI feature in Flask >= 0.11`_.
If you're using Flask < 0.10 you'll need to install a backport package
called `Flask-CLI`_ as well, e.g.::

    pip install Flask-CLI

Or install it in one go::

    pip install Flask-RQ2[cli]

Please call ``flask rq --help`` for more information, assuming
you've set the ``FLASK_APP`` environment variable to the Flask app path.

Commands
~~~~~~~~

There isn't an official overview of CLI commands in the RQ documentation,
but these are the commands that Flask-RQ2 support.

- ``worker`` -- Starts an `RQ worker`_ (required to run jobs).

- ``scheduler`` -- Starts an `RQ Scheduler`_ (optional for scheduled jobs).

- ``info`` -- Shows an `RQ command-line monitor`_.

- ``empty`` -- Empty the given `RQ queues`_.

- ``requeue`` -- Requeues `failed jobs`_.

- ``suspend`` -- Suspends all workers.

- ``resume`` -- Resumes all workers.

Please call each command with the ``--help`` option to learn more about their
required and optional paramaters.

Configuration
-------------

``RQ_REDIS_URL``
~~~~~~~~~~~~~~~~

The URL to pass to the :meth:`~redis.StrictRedis.from_url` method of the
redis-py_'s connection class as defind in ``RQ_CONNECTION_CLASS``.
Defaults to connecting to the local Redis instance, database 0.

.. code-block:: python

    app.config['RQ_REDIS_URL'] = 'redis://localhost:6379/0'

``RQ_CONNECTION_CLASS``
~~~~~~~~~~~~~~~~~~~~~~~

The dotted import path to the redis-py_ client class to connect to the Redis
server using the ``RQ_REDIS_URL`` configuration value.

.. code-block:: python

    app.config['RQ_CONNECTION_CLASS'] = 'myproject.backends.MyStrictRedis'

Defaults to ``'redis.StrictRedis'``.

``RQ_QUEUES``
~~~~~~~~~~~~~

The default queues that the worker and CLI commands (``empty``, ``info`` and
``worker``) act on by default.

.. code-block:: python

    app.config['RQ_QUEUES'] = ['default']

``RQ_ASYNC``
~~~~~~~~~~~~

Whether or not to run jobs asynchronously. Defaults to ``True`` meaning
that jobs only run when they are processed by the workers.

.. code-block:: python

    app.config['RQ_ASYNC'] = True

Set to ``False`` to run jobs immediatedly upon enqueuing in-process.
This may be useful for testing purposes or other constrained environments.
This is the main switch, use with discretion.

``RQ_QUEUE_CLASS``
~~~~~~~~~~~~~~~~~~

.. versionadded:: 17.1

The dotted import path of the queue class to enqueue jobs with.

.. code-block:: python

    app.config['RQ_QUEUE_CLASS'] = 'myproject.queue.MyQueue'

Defaults to ``'rq.queue.Queue'``.

``RQ_WORKER_CLASS``
~~~~~~~~~~~~~~~~~~~

.. versionadded:: 17.1

The dotted import path of the worker class to process jobs with.

.. code-block:: python

    app.config['RQ_WORKER_CLASS'] = 'myproject.worker.MyWorker'

Defaults to ``'rq.worker.Worker'``.

``RQ_JOB_CLASS``
~~~~~~~~~~~~~~~~

.. versionadded:: 17.1

The dotted import path of the job class for RQ jobs.

.. note::

    This **must** be a subclass of ``flask_rq2.job.FlaskJob`` or
    otherwise Flask-RQ2 won't work.

.. code-block:: python

    app.config['RQ_JOB_CLASS'] = 'myproject.job.MyFlaskJob'

Defaults to ``'flask_rq2.job.FlaskJob'``.

``RQ_SCHEDULER_CLASS``
~~~~~~~~~~~~~~~~~~~~~~

.. versionadded:: 17.1

The dotted import path of the scheduler class to enqueue scheduled jobs with.

.. code-block:: python

    app.config['RQ_SCHEDULER_CLASS'] = 'myproject.scheduler.MyScheduler'

Defaults to ``'rq_scheduler.Scheduler'``.

``RQ_SCHEDULER_QUEUE``
~~~~~~~~~~~~~~~~~~~~~~

The name of the queue to enqueue scheduled jobs in.

.. code-block:: python

    app.config['RQ_SCHEDULER_QUEUE'] = 'scheduled'

Defaults to ``'default'``.

``RQ_SCHEDULER_INTERVAL``
~~~~~~~~~~~~~~~~~~~~~~~~~

The default interval the RQ Scheduler checks for jobs to enqueue, in seconds.

.. code-block:: python

    app.config['RQ_SCHEDULER_INTERVAL'] = 1

Defaults to ``60``.

.. _`Flask-CLI`: http://pythonhosted.org/Flask-CLI/
.. _Click: http://click.pocoo.org/
.. _`CLI feature in Flask >= 0.11`: http://flask.pocoo.org/docs/dev/cli/
.. _`RQ queues`: http://python-rq.org/docs/
.. _`RQ worker`: http://python-rq.org/docs/workers/
.. _`RQ Scheduler`: https://github.com/ui/rq-scheduler
.. _`RQ command-line monitor`: http://python-rq.org/docs/monitoring/
.. _`failed jobs`: http://python-rq.org/docs/exceptions/
.. _redis-py: https://pypi.python.org/pypi/redis

Changelog
---------

.. include:: ../CHANGELOG.rst
   :start-after: .. snip

Other content
-------------

.. toctree::
   :maxdepth: 3

   api
