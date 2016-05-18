from click.testing import CliRunner
from flask import Flask

import pytest
from flask_cli import FlaskCLI

from flask_rq2 import RQ


class Config(object):
    RQ_REDIS_URL = 'redis://localhost:6379/15'
    RQ_QUEUES = ['test-queue']
    RQ_ASYNC = False
    RQ_SCHEDULER_QUEUE = 'scheduler-queue'
    RQ_SCHEDULER_INTERVAL = 42


def create_app(config=None):
    app = Flask('testapp')
    if config is not None:
        app.config.from_object(config)
    return app


@pytest.fixture
def config():
    return Config()


@pytest.fixture
def app(request, config):
    app = create_app(config)
    ctx = app.app_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    return app


@pytest.fixture
def rq(app):
    return RQ(app)


@pytest.fixture
def rq_cli_app(app):
    FlaskCLI(app)
    app.cli.name = app.name
    RQ(app)
    return app


@pytest.fixture
def cli_runner():
    return CliRunner()
