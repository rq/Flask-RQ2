# -*- coding: utf-8 -*-
"""
    flask_rq2.script
    ~~~~~~~~~~~~~~~~

    Support for the argparse based Flask-Script CLI.
    It wraps the CLI of RQ with the properly configured worker, queue and job
    classes.

"""
import operator
import os
import re

from flask.ext.script import Command, Manager, Option

from rq.cli import cli

try:
    from rq_scheduler import Scheduler
    from rq_scheduler.utils import setup_loghandlers
except ImportError:  # pragma: no cover
    Scheduler = None


_commands = {}


class RQCommand(Command):

    def __init__(self, rq):
        self.rq = rq

    def __call__(self, app=None, *args, **kwargs):
        """
        Handles the command with the given app.
        Default behaviour is to call ``self.run`` within a test request
        context.
        This will also init the Flask-RQ interface module.
        """
        with app.test_request_context():
            return self.run(*args, **kwargs)

    @classmethod
    def register(cls, condition=True):

        def wrapper(cls):
            if hasattr(cls, 'name'):
                name = cls.name
            else:
                name = cls.__name__.lower()
                name = re.sub(r'command$', '', name)
            if condition:
                _commands[name] = cls
            return cls
        return wrapper


@RQCommand.register()
class EmptyCommand(RQCommand):
    "Empty given queues."

    option_list = [
        Option('--all', '-a', action='store_true', dest='_all',
               help='Empty all queues'),
        Option('queues', nargs='*', metavar='QUEUE',
               help='Queues to work with, defaults to the ones specified '
                    'in the Flask app config'),
    ]

    def run(self, _all, queues):
        cli.empty.callback(
            url=self.rq.url,
            all=_all,
            queues=queues or self.rq.queues,
        )


@RQCommand.register()
class RequeueCommand(RQCommand):
    "Requeue failed jobs."

    option_list = [
        Option('--all', '-a', action='store_true', dest='_all',
               help='Requeue all failed jobs'),
        Option('job_ids', nargs='*', metavar='JOB_ID'),
    ]

    def run(self, _all, job_ids):
        cli.requeue.callback(
            url=self.rq.url,
            all=_all,
            job_ids=job_ids,
        )


@RQCommand.register()
class InfoCommand(RQCommand):
    "RQ command-line monitor."

    option_list = [
        Option('--path', '-P', default='.', help='Specify the import path.'),
        Option('--interval', '-i',
               type=float,
               help='Updates stats every N seconds (default: don\'t poll)'),
        Option('--raw', '-r',
               action='store_true',
               help='Print only the raw numbers, no bar charts'),
        Option('--only-queues', '-Q',
               action='store_true', help='Show only queue info'),
        Option('--only-workers', '-W',
               action='store_true', help='Show only worker info'),
        Option('--by-queue', '-R',
               action='store_true', help='Shows workers by queue'),
        Option('queues', nargs='*', metavar='QUEUE',
               help='Queues to work with, defaults to the ones specified '
                    'in the Flask app config'),
    ]

    def run(self, path, interval, raw, only_queues, only_workers, by_queue,
            queues):
        cli.info.callback(
            url=self.rq.url,
            config=None,
            path=path,
            interval=interval,
            raw=raw,
            only_queues=only_queues,
            only_workers=only_workers,
            by_queue=by_queue,
            queues=queues or self.rq.queues,
        )


@RQCommand.register()
class WorkerCommand(RQCommand):
    "Starts an RQ worker."

    option_list = (
        Option('--burst', '-b', action='store_true',
               help='Run in burst mode (quit after all work is done)'),
        Option('--name', '-n', help='Specify a different name'),
        Option('--path', '-P', default='.', help='Specify the import path.'),
        Option('--results-ttl', type=int,
               help='Default results timeout to be used'),
        Option('--worker-ttl', type=int,
               help='Default worker timeout to be used'),
        Option('--verbose', '-v', action='store_true',
               help='Show more output'),
        Option('--quiet', '-q', action='store_true', help='Show less output'),
        Option('--exception-handler', type=list,
               help='Exception handler(s) to use', action='append'),
        Option('--pid', metavar='FILE',
               help='Write the process ID number '
                    'to a file at the specified path'),
        Option('queues', nargs='*', metavar='QUEUE',
               help='Queues to work with, defaults to the ones specified '
                    'in the Flask app config')
    )

    def run(self, burst, name, path, results_ttl, worker_ttl, verbose,
            quiet, exception_handler, pid, queues):
        cli.worker.callback(
            url=self.rq.url,
            config=None,
            burst=burst,
            name=name,
            worker_class=self.rq.app_worker_path,
            job_class=self.rq.app_job_path,
            queue_class=self.rq.app_queue_path,
            path=path,
            results_ttl=results_ttl,
            worker_ttl=worker_ttl,
            verbose=verbose,
            quiet=quiet,
            sentry_dsn=None,
            exception_handler=exception_handler or self.rq._exception_handlers,
            pid=pid,
            queues=queues or self.rq.queues,
        )


@RQCommand.register()
class SuspendCommand(RQCommand):
    "Suspends all workers."

    option_list = [
        Option('--duration',
               help='Seconds you want the workers to be suspended. '
                    'Default is forever.',
               type=int)
    ]

    def run(self, duration):
        cli.suspend.callback(url=self.rq.url, config=None, duration=duration)


@RQCommand.register()
class ResumeCommand(RQCommand):
    "Resumes all workers."

    def run(self):
        cli.resume.callback(url=self.rq.url, config=None)


@RQCommand.register(condition=Scheduler is not None)
class SchedulerCommand(RQCommand):
    "Periodically checks for scheduled jobs."

    option_list = [
        Option('--verbose', '-v', action='store_true',
               help='Show more output'),
        Option('-i', '--interval', default=60.0, type=float, metavar='SECONDS',
               help='How often the scheduler checks for new jobs to add to '
                    'the queue (in seconds, can be floating-point for more '
                    'precision).'),
        Option('--pid', metavar='FILE',
               help='Write the process ID number '
                    'to a file at the specified path'),
    ]

    def run(self, verbose, interval, pid):
        scheduler = self.rq.get_scheduler(interval)
        if pid:
            with open(os.path.expanduser(pid), 'w') as fp:
                fp.write(str(os.getpid()))
        if verbose:
            level = 'DEBUG'
        else:
            level = 'INFO'
        setup_loghandlers(level)
        scheduler.run()


class RQManager(Manager):
    """
    To use in your own management script, add the following::

        from flask.ext.script import Manager
        from flask.ext.rq2.script import RQManager

        from app import create_app
        from jobs import rq

        app = create_app()

        manager = Manager(app)
        manager.add_command('rq', RQManager(rq))

    Then you'll be able to call ``python manage.py rq info`` etc.

    Please call ``python manage.py rq --help`` for more infomation.
    """
    def __init__(self, rq, *args, **kwargs):
        self.rq = rq
        kwargs.setdefault('usage', 'RQ command line tool.')
        super(RQManager, self).__init__(*args, **kwargs)
        for name, cls in sorted(_commands.items(), key=operator.itemgetter(0)):
            self.add_command(name, cls(rq))
