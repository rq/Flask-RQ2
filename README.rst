Flask-RQ2
=========

.. image:: https://readthedocs.org/projects/flask-rq2/badge/?version=latest
   :target: https://flask-rq2.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://travis-ci.org/jezdez/Flask-RQ2.svg?branch=master
   :target: https://travis-ci.org/jezdez/Flask-RQ2
   :alt: Test Status

.. image:: https://codecov.io/gh/jezdez/Flask-RQ2/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/jezdez/Flask-RQ2
   :alt: Test Coverage Status

Resources
---------

- `Documentation <https://flask-rq2.readthedocs.io/>`_
- `Issue Tracker <https://github.com/jezdez/flask-rq2/issues>`_
- `Code <https://github.com/jezdez/flask-rq2/>`_

.. snip

A Flask extension for RQ_ (Redis Queue).

This is a continuation of `Flask-RQ`_ more in spirit than in code. Many thanks
to `Matt Wright`_ for the inspiration and providing the shoulders to stand on.

.. _`RQ`: http://python-rq.org/
.. _`Flask-RQ`: https://github.com/mattupstate/flask-rq
.. _`Matt Wright`: https://github.com/mattupstate

Installation
------------

.. code-block:: console

    pip install Flask-RQ2

Getting started
---------------

To quickly start using Flask-RQ2, simply create an ``RQ`` instance:

.. code-block:: python

    from flask import Flask
    from flask.ext.rq2 import RQ

    app = Flask(__name__)
    rq = RQ(app)

Alternatively, if you're using the `application factory`_ pattern:

.. code-block:: python

    from flask.ext.rq2 import RQ
    rq = RQ()

and then later call ``init_app`` where you create your application object:

.. code-block:: python

    from flask import Flask

    def create_app():
        app = Flask(__name__)

        from yourapplication.jobs import rq
        rq.init_app(app)

        # more here..
        return app

.. _`application factory`: http://flask.pocoo.org/docs/0.10/patterns/appfactories/

Decorators
----------

``@job``
~~~~~~~~

A decorator to mark a function as an `RQ job`_ and to add some helpers to
the function to simplify enqueuing:

.. code-block:: python

    from flask.ext.rq2 import RQ

    rq = RQ()

    @rq.job
    def add(x, y):
        return x + y

Then in your app code:

.. code-block:: python

    job = add.queue(1, 2)

A specific queue name can also be passed as argument:

.. code-block:: python

    @rq.job('low')
    def add(x, y):
        return x + y

Some other parameters are available as well:

.. code-block:: python

    @rq.job('low', timeout=180, results_ttl=60*60, ttl=60*60*24)
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

    # queue job every day at noon (UTC!)
    add.cron('0 0 12 * * ?', 'add-one-two', 1, 2)

See the full `API docs`_ for more information.

.. _`API docs`: http://flask-rq2.readthedocs.io/en/stable/api/
.. _`RQ job`: http://python-rq.org/docs/jobs/

``@exception_handler``
~~~~~~~~~~~~~~~~~~~~~~

An optional decorator for `custom exception handlers`_ that the RQ worker
should call when catching exceptions during job execution.

.. code-block:: python

    from flask.ext.rq2 import RQ

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

    from flask.ext.rq2 import RQ

    rq = RQ()

    default_queue = rq.get_queue()
    low_queue = rq.get_queue('low')

    easy_job = default_queue.enqueue(add, args=(1, 2))
    hard_job = low_queue.enqueue(add, args=(1e100, 2e200))

``get_worker``
~~~~~~~~~~~~~~

Returns a worker for default queue or specific queues for names given as arguments:

.. code-block:: python

    from flask.ext.rq2 import RQ

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

    from flask.ext.rq2 import RQ

    rq = RQ()

    # check every 10 seconds if there are any jobs to enqueue
    scheduler = rq.get_scheduler(interval=10)
    scheduler.run()

CLI support
-----------

Flask-RQ2 supports both the (upcoming) Click_ based
`CLI feature in Flask >= 1.0`_ (including the backport to Flask < 1.0 in
`Flask-CLI`_) as well as `Flask-Script`_.

Flask CLI
~~~~~~~~~

For the Flask CLI to work it's recommended to install the `Flask-CLI`_ package
since it contains a import shim to automatically import CLI code from
Flask in case >= 1.0 is installed. That means this is the most future proof
option for you.

The rest happens automatically: a new ``rq`` subcommand will be added to the
``flask`` command that wraps RQ's own ``rq`` CLI tool using the Flask
configuration values.

Please call ``flask rq --help`` for more infomation, assuming
you've set the ``FLASK_APP`` environment variable to the Flask app path.

You can install the dependencies for this using this shortcut:

.. code-block:: console

    pip install Flask-RQ2[cli]

Flask-Script
~~~~~~~~~~~~

`Flask-Script`_ works a bit different and requires you to manually register a
command manager with the main script manager. For example:

.. code-block:: python

    from flask.ext.script import Manager
    from flask.ext.rq2.script import RQManager

    from app import create_app
    from jobs import rq  # a flask.ext.rq2.RQ instance

    app = create_app()

    manager = Manager(app)
    manager.add_command('rq', RQManager(rq))

That adds a ``rq`` subcommand to your management script and wraps RQ's own
``rq`` CLI tools automatically using the Flask configuration values.

Please call ``python manage.py rq --help`` for more infomation, assuming
your management script is called ``manage.py``.

You can also install the dependencies for this using this shortcut:

.. code-block:: console

    pip install Flask-RQ2[script]

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

.. _`Flask-CLI`: http://pythonhosted.org/Flask-CLI/
.. _Click: http://click.pocoo.org/
.. _`CLI feature in Flask >= 1.0`: http://flask.pocoo.org/docs/dev/cli/
.. _`Flask-Script`: https://flask-script.readthedocs.io/
.. _`RQ queues`: http://python-rq.org/docs/
.. _`RQ worker`: http://python-rq.org/docs/workers/
.. _`RQ Scheduler`: https://github.com/ui/rq-scheduler
.. _`RQ command-line monitor`: http://python-rq.org/docs/monitoring/
.. _`failed jobs`: http://python-rq.org/docs/exceptions/

Configuration
-------------

``RQ_REDIS_URL``
~~~~~~~~~~~~~~~~

The URL to pass to redis-py's ``Redis.from_url`` classmethod to create a
Redis connetion pool. Defaults to connecting to the local Redis instance,
database 0.

.. code-block:: python

    app.config['RQ_REDIS_URL'] = 'redis://localhost:6379/0'

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

``RQ_SCHEDULER_QUEUE``
~~~~~~~~~~~~~~~~~~~~~~

The queue to enqueue scheduled jobs in.

.. code-block:: python

    app.config['RQ_SCHEDULER_QUEUE'] = 'scheduled'

Defaults to ``'default'``.

``RQ_SCHEDULER_INTERVAL``
~~~~~~~~~~~~~~~~~~~~~~~~~

The default interval the RQ Scheduler checks for jobs to enqueue.

.. code-block:: python

    app.config['RQ_SCHEDULER_INTERVAL'] = 1

Defaults to ``60``.
