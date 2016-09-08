import os
from click.testing import CliRunner

import pytest

from flask_rq2 import RQ


class Config(object):
    RQ_REDIS_URL = 'redis://localhost:6379/15'
    RQ_QUEUES = ['test-queue']
    RQ_ASYNC = False
    RQ_SCHEDULER_QUEUE = 'scheduler-queue'
    RQ_SCHEDULER_INTERVAL = 42


def create_app(config=None):
    from cliapp.app import testapp
    if config is not None:
        testapp.config.from_object(config)
    return testapp


@pytest.fixture
def config():
    return Config()


@pytest.fixture
def test_apps(monkeypatch):
    monkeypatch.syspath_prepend(
        os.path.abspath(os.path.join(
            os.path.dirname(__file__), 'test_apps'))
    )


@pytest.fixture
def app(request, config, test_apps, monkeypatch):
    app = create_app(config)
    ctx = app.app_context()
    ctx.push()

    def teardown():
        ctx.pop()

    request.addfinalizer(teardown)
    monkeypatch.setenv('FLASK_APP', 'cliapp.app:testapp')
    return app


@pytest.fixture
def rq(app):
    return RQ(app)


@pytest.fixture
def rq_cli_app(app):
    app.cli.name = app.name
    RQ(app)
    return app


@pytest.fixture
def cli_runner():
    return CliRunner()
