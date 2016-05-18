import logging
import sys
from flask import current_app

import pytest

from flask_rq2 import app as flask_rq2_app
from flask_rq2 import script as flask_rq2_script
from flask_rq2 import RQ
from flask_rq2.script import RQCommand, RQManager, _commands


def test_with_rq_commands(rq):
    manager = RQManager(rq)
    assert set(_commands.keys()) == set(manager._commands.keys())
    for command in manager._commands.values():
        assert command.rq == rq


def test_extra_command(rq, monkeypatch):
    monkeypatch.setattr(flask_rq2_script, '_commands', {})

    @RQCommand.register()
    class TestRQCommand(RQCommand):
        name = 'testrq'

        def run(self):
            assert self.app
    assert 'testrq' in flask_rq2_script._commands


def test_decorator_condition(monkeypatch):
    monkeypatch.setattr(flask_rq2_script, '_commands', {})

    @RQCommand.register(False)
    class FalseCommand(RQCommand):
        def run(self):
            assert self.app

    assert 'false' not in flask_rq2_script._commands.keys()


def test_app_context(app):
    rq = RQ(app)

    class ContextCommand(RQCommand):
        def run(self):
            assert current_app == app
            return current_app.name

    command = ContextCommand(rq)
    assert command.rq == rq

    result = command(app)
    assert result == app.name


@pytest.mark.parametrize('command,output,uses_logging', [
    ('empty', '0 jobs removed from', False),
    ('requeue', 'Nothing to do', False),
    ('info', '1 queues, 0 jobs total', False),
    ('worker --burst', 'Listening on', True),
    ('suspend', 'Suspending workers', False),
    ('resume', 'Resuming workers', False),
])
def test_commands(command, output, uses_logging, app, caplog, capsys,
                  monkeypatch, request):
    rq = RQ(app)
    manager = RQManager(app=app, rq=rq)
    monkeypatch.setattr(sys, 'argv', ['manage.py'] + command.split())
    try:
        manager.run()
    except SystemExit as e:
        exit_code = e.code
    else:
        exit_code = None
    assert exit_code == 0
    if uses_logging:
        caplog.setLevel(logging.INFO, logger='rq.worker')
        out = caplog.text()
    else:
        out, err = capsys.readouterr()
    assert output in out

    def flush():
        rq.connection.flushdb()
    request.addfinalizer(flush)


def test_scheduler_command_pid(config, app, monkeypatch, tmpdir):
    monkeypatch.setattr(flask_rq2_app.Scheduler, 'run',
                        lambda *args, **kwargs: None)
    rq = RQ(app)
    manager = RQManager(app=app, rq=rq)
    pid = tmpdir.join('rq2_scheduler.pid')
    assert not pid.exists()
    monkeypatch.setattr(sys, 'argv', ['rq', 'scheduler', '--pid', pid.strpath])
    try:
        manager.run()
    except SystemExit as e:
        exit_code = e.code
    else:
        exit_code = None
    assert exit_code == 0
    assert pid.read() != ''


def test_scheduler_command_verbose(config, app, monkeypatch):
    monkeypatch.setattr(flask_rq2_app.Scheduler, 'run',
                        lambda *args, **kwargs: None)
    rq = RQ(app)
    manager = RQManager(app=app, rq=rq)

    def setup_loghandlers(level):
        assert level == 'DEBUG'
    monkeypatch.setattr(flask_rq2_script, 'setup_loghandlers',
                        setup_loghandlers)

    monkeypatch.setattr(sys, 'argv', ['rq', 'scheduler', '--verbose'])
    try:
        manager.run()
    except SystemExit as e:
        exit_code = e.code
    else:
        exit_code = None
    assert exit_code == 0
