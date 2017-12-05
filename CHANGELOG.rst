Changelog
---------

https://img.shields.io/badge/calver-YY.0M.MICRO-22bfda.svg

Flask-RQ2 follows the `CalVer <http://calver.org/>`_ version specification
in the form of::

  YY.Minor[.Micro]

E.g.::

  16.1.1

.. snip

17.2 (2017.12.05)
~~~~~~~~~~~~~~~~~

- Allow dynamically setting timeout, result TTL and job TTL and other
  parameters when enqueuing, scheduling or adding as a cron job.

17.1 (2017-12-05)
~~~~~~~~~~~~~~~~~

- Require Flask >= 0.10, but it's recommended to use at least 0.11.

- Require rq 0.8.0 or later and rq-scheduler 0.7.0 or later.

- Require setting ``FLASK_APP`` environment variable to load Flask app
  during job performing.

- Add ``RQ_SCHEDULER_CLASS``, ``RQ_WORKER_CLASS``, ``RQ_JOB_CLASS`` and
  ``RQ_QUEUE_CLASS`` as configuration values.

- Add support for rq-scheduler's ``--burst`` option to automatically quit
  after all work is done.

- Drop support for Flask-Script in favor of native Flask CLI support
  (or via Flask-CLI app for Flask < 0.11).

- Drop support for Python 3.4.

- Allow setting the queue dynamically when enqueuing, scheduling or adding
  as a cron job.

- Handle the result_ttl and queue_name job overrides better.

- Actually respect the ``RQ_SCHEDULER_INTERVAL`` config value.

- Move ``flask_rq2.helpers`` module to ``flask_rq2.functions``.

- Use a central Redis client and require app initialization before connecting.
  You'll have to run ``RQ.init_app`` **before** you can queue or schedule
  a job from now on.

17.0 (2017-02-15)
~~~~~~~~~~~~~~~~~

- Pin the rq version Flask-RQ2 depends on to >=0.6.0,<0.7.0 for now.
  A bigger refactor will follow shortly that fixes those problems better.

- Allow overriding the `default_timeout` in case of using the
  factory pattern.

- Run tests on Python 3.6.

16.1.1 (2016-09-08)
~~~~~~~~~~~~~~~~~~~

- Fix typos in docs.

16.1 (2016-09-08)
~~~~~~~~~~~~~~~~~

- Official Support for Flask >= 0.11

- Fix import paths to stop using ``flask.ext`` prefix.

16.0.2 (2016-05-20)
~~~~~~~~~~~~~~~~~~~

- Fix package description.

16.0.1 (2016-05-20)
~~~~~~~~~~~~~~~~~~~

- Make wheel file universal.

16.0 (2016-05-20)
~~~~~~~~~~~~~~~~~

- Initial release.
