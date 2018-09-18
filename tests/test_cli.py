import logging

import click

import pytest
from flask_cli import FlaskGroup, ScriptInfo, cli
from flask_rq2 import app as flask_rq2_app
from flask_rq2 import cli as flask_rq2_cli
from flask_rq2 import scheduler as flask_rq2_scheduler
from flask_rq2.cli import _commands, add_commands


def test_click_missing_raises(app, rq, monkeypatch):
    monkeypatch.setattr(flask_rq2_app, 'click', None)
    with pytest.raises(RuntimeError):
        rq.init_cli(app)


def test_cli_init(rq_cli_app, rq):
    assert cli is not None
    assert _commands != {}
    assert 'rq' not in cli.commands
    assert 'rq' in rq_cli_app.cli.commands


def test_cli_custom_init(rq):
    @click.group(cls=FlaskGroup)
    def cli():
        pass

    assert 'rq' not in cli.commands
    add_commands(cli, rq)
    assert 'rq' in cli.commands


def test_empty_command(config, rq_cli_app, cli_runner):
    obj = ScriptInfo(create_app=lambda info: rq_cli_app)
    result = cli_runner.invoke(rq_cli_app.cli, args=['rq', 'empty'], obj=obj)
    assert result.exit_code == 0
    assert ('0 jobs removed from %s queue' % config.RQ_QUEUES[0] in
            result.output)


def test_requeue_command(config, rq_cli_app, cli_runner):
    obj = ScriptInfo(create_app=lambda info: rq_cli_app)
    result = cli_runner.invoke(rq_cli_app.cli, args=['rq', 'requeue'], obj=obj)
    assert result.exit_code == 0
    assert 'Nothing to do' in result.output


def test_info_command(config, rq_cli_app, cli_runner):
    obj = ScriptInfo(create_app=lambda info: rq_cli_app)
    result = cli_runner.invoke(rq_cli_app.cli, args=['rq', 'info'], obj=obj)
    assert result.exit_code == 0
    assert config.RQ_QUEUES[0] in result.output
    assert '1 queues, 0 jobs total' in result.output


def test_worker_command(config, rq_cli_app, cli_runner, caplog):
    caplog.set_level(logging.INFO, logger='rq.worker')
    obj = ScriptInfo(create_app=lambda info: rq_cli_app)
    result = cli_runner.invoke(rq_cli_app.cli,
                               args=['rq', 'worker', '--burst',
                                     '--worker-ttl', '10'],
                               obj=obj)
    assert result.exit_code == 0
    out = caplog.text
    assert result.output == ''
    assert 'Listening on %s' % config.RQ_QUEUES[0] in out


def test_suspend_command(config, rq_cli_app, cli_runner):
    obj = ScriptInfo(create_app=lambda info: rq_cli_app)
    result = cli_runner.invoke(rq_cli_app.cli, args=['rq', 'suspend'], obj=obj)
    assert result.exit_code == 0
    assert 'Suspending workers' in result.output


def test_resume_command(config, rq_cli_app, cli_runner):
    obj = ScriptInfo(create_app=lambda info: rq_cli_app)
    result = cli_runner.invoke(rq_cli_app.cli, args=['rq', 'resume'], obj=obj)
    assert result.exit_code == 0
    assert 'Resuming workers' in result.output


def test_scheduler_command(config, rq_cli_app, cli_runner):
    obj = ScriptInfo(create_app=lambda info: rq_cli_app)
    result = cli_runner.invoke(rq_cli_app.cli,
                               args=['rq', 'scheduler', '--help'],
                               obj=obj)
    assert result.exit_code == 0
    assert 'Periodically checks for scheduled jobs' in result.output


def test_scheduler_command_default_interval(config, app, cli_runner,
                                            monkeypatch):
    class CustomRQ(flask_rq2_app.RQ):
        def get_scheduler(self, interval=None, queue=None):
            # the passed interval must be None
            assert interval is None
            scheduler = super(CustomRQ, self).get_scheduler(interval=interval,
                                                            queue=queue)
            assert scheduler._interval == self.scheduler_interval
            return scheduler

    CustomRQ(app)
    app.cli.name = app.name

    monkeypatch.setattr(flask_rq2_scheduler.FlaskScheduler, 'run',
                        lambda *args, **kwargs: None)
    obj = ScriptInfo(create_app=lambda info: app)
    result = cli_runner.invoke(app.cli, args=['rq', 'scheduler'], obj=obj)
    assert result.exit_code == 0


def test_scheduler_command_override_interval(config, app, cli_runner,
                                             monkeypatch):
    test_interval = 10

    class CustomRQ(flask_rq2_app.RQ):
        def get_scheduler(self, interval=None, queue=None):
            assert interval == test_interval
            return super(CustomRQ, self).get_scheduler(interval=interval,
                                                       queue=queue)

    rq = CustomRQ(app)
    app.cli.name = app.name
    assert test_interval != rq.scheduler_interval

    monkeypatch.setattr(flask_rq2_scheduler.FlaskScheduler, 'run',
                        lambda *args, **kwargs: None)
    obj = ScriptInfo(create_app=lambda info: app)
    result = cli_runner.invoke(app.cli,
                               args=['rq', 'scheduler', '--interval',
                                     test_interval],
                               obj=obj)
    assert result.exit_code == 0


def test_scheduler_command_pid(config, rq_cli_app, cli_runner, monkeypatch,
                               tmpdir):
    monkeypatch.setattr(flask_rq2_scheduler.FlaskScheduler, 'run',
                        lambda *args, **kwargs: None)
    obj = ScriptInfo(create_app=lambda info: rq_cli_app)
    pid = tmpdir.join('rq2_scheduler.pid')
    args = ['rq', 'scheduler', '--pid', pid.strpath]
    assert not pid.exists()
    result = cli_runner.invoke(rq_cli_app.cli, args=args, obj=obj)
    assert result.exit_code == 0
    assert pid.read() != ''


def test_scheduler_command_verbose(config, rq_cli_app, cli_runner,
                                   monkeypatch):
    obj = ScriptInfo(create_app=lambda info: rq_cli_app)
    monkeypatch.setattr(flask_rq2_scheduler.FlaskScheduler, 'run',
                        lambda *args, **kwargs: None)

    def setup_loghandlers(level):
        assert level == 'DEBUG'

    monkeypatch.setattr(flask_rq2_cli, 'setup_loghandlers', setup_loghandlers)

    args = ['rq', 'scheduler', '--verbose']
    result = cli_runner.invoke(rq_cli_app.cli, args=args, obj=obj)
    assert result.exit_code == 0


def test_scheduler_command_scheduler_missing(config, rq_cli_app, cli_runner,
                                             monkeypatch):
    monkeypatch.setattr(flask_rq2_cli, 'Scheduler', None)
    obj = ScriptInfo(create_app=lambda info: rq_cli_app)
    result = cli_runner.invoke(rq_cli_app.cli,
                               args=['rq', 'scheduler', '--help'],
                               obj=obj)
    assert result.exit_code == 0
    assert 'Periodically checks for scheduled jobs' in result.output


def test_rq_command_decorator(monkeypatch):
    monkeypatch.setattr(flask_rq2_cli, '_commands', {})

    @flask_rq2_cli.rq_command()
    def test():
        pass
    assert test in flask_rq2_cli._commands.values()


def test_rq_command_decorator_condition(monkeypatch):
    monkeypatch.setattr(flask_rq2_cli, '_commands', {})

    @flask_rq2_cli.rq_command(False)
    def test():
        pass
    assert test not in flask_rq2_cli._commands.values()
