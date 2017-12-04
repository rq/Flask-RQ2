Changelog
---------

https://img.shields.io/badge/calver-YY.0M.MICRO-22bfda.svg

Flask-RQ2 follows the `CalVer <http://calver.org/>`_ version specification
in the form of::

  YY.Minor[.Micro]

E.g.::

  16.1.1

.. snip

17.1 (2017-12-04)
~~~~~~~~~~~~~~~~~

- Requires Flask >= 0.10, but it's recommended to use at least 0.11.

- Requires rq 0.8.0 or later and rq-scheduler 0.7.0 or later.

- Requires setting ``FLASK_APP`` environment variable to load Flask app
  during job performing.

- Revamped the way how the app context is created when running the jobs
  to use FLASK_APP.

- Added ``RQ_SCHEDULER_CLASS``, ``RQ_WORKER_CLASS``, ``RQ_JOB_CLASS`` and
  ``RQ_QUEUE_CLASS`` as configuration values.

- Added support for rq-scheduler's ``--burst`` option to automatically quit
  after all work is done.

- Dropped support for Flask-Script in favor of native Flask CLI support
  (or via Flask-CLI app for Flask < 0.11).

- Dropped support for Python 3.4.

17.0 (2017-02-15)
~~~~~~~~~~~~~~~~~

- Pinned the rq version Flask-RQ2 depends on to >=0.6.0,<0.7.0 for now.
  A bigger refactor will follow shortly that fixes those problems better.

- Allow overriding the `default_timeout` in case of using the
  factory pattern.

- Run tests on Python 3.6.

16.1.1 (2016-09-08)
~~~~~~~~~~~~~~~~~~~

- Fixed typos in docs.

16.1 (2016-09-08)
~~~~~~~~~~~~~~~~~

- Official Support for Flask >= 0.11

- Fixed import paths to stop using ``flask.ext`` prefix.

16.0.2 (2016-05-20)
~~~~~~~~~~~~~~~~~~~

- Fixed package description.

16.0.1 (2016-05-20)
~~~~~~~~~~~~~~~~~~~

- Made wheel file universal.

16.0 (2016-05-20)
~~~~~~~~~~~~~~~~~

- Initial release.
