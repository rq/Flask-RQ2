# -*- coding: utf-8 -*-
"""
    flask_rq2.job
    ~~~~~~~~~~~~~

    The Flask application aware RQ job class.

"""
from flask import current_app
from rq.job import Job

try:
    from flask.cli import ScriptInfo
except ImportError:  # pragma: no cover
    try:
        from flask_cli import ScriptInfo
    except ImportError:
        raise RuntimeError('Cannot import Flask CLI. Is it installed?')


class FlaskJob(Job):
    """
    The RQ Job class that is capable to running with a Flask app
    context. This requires setting the ``FLASK_APP`` environment
    variable.
    """
    def __init__(self, *args, **kwargs):
        super(FlaskJob, self).__init__(*args, **kwargs)
        self.script_info = ScriptInfo()

    def load_app(self):
        if current_app:
            app = current_app
        else:
            app = self.script_info.load_app()
        return app

    def perform(self):
        app = self.load_app()
        with app.app_context():
            return super(FlaskJob, self).perform()
