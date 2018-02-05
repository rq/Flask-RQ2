Flask-RQ2
=========

.. image:: https://readthedocs.org/projects/flask-rq2/badge/?version=latest
   :target: https://flask-rq2.readthedocs.io/en/latest/?badge=latest
   :alt: Documentation Status

.. image:: https://travis-ci.org/rq/Flask-RQ2.svg?branch=master
   :target: https://travis-ci.org/rq/Flask-RQ2
   :alt: Test Status

.. image:: https://codecov.io/gh/rq/Flask-RQ2/branch/master/graph/badge.svg
   :target: https://codecov.io/gh/rq/Flask-RQ2
   :alt: Test Coverage Status

.. image:: https://img.shields.io/badge/calver-YY.MINOR.MICRO-22bfda.svg
   :target: https://calver.org/
   :alt: CalVer - Timely Software Versioning

Resources
---------

- `Documentation <https://flask-rq2.readthedocs.io/>`_
- `Issue Tracker <https://github.com/rq/flask-rq2/issues>`_
- `Code <https://github.com/rq/flask-rq2/>`_
- `Continuous Integration <https://travis-ci.org/rq/Flask-RQ2>`_

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
    from flask_rq2 import RQ

    app = Flask(__name__)
    rq = RQ(app)

Alternatively, if you're using the `application factory`_ pattern:

.. code-block:: python

    from flask_rq2 import RQ
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

.. snap

For more information see the `full documentation
<https://flask-rq2.readthedocs.io/>`_  on Read The Docs.
