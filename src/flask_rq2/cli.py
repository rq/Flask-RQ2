# -*- coding: utf-8 -*-
"""
    flask_rq2.cli
    ~~~~~~~~~~~~~

    Support for the Click based Flask CLI via Flask-CLI.

"""
import operator
import os
from functools import update_wrapper

import click
from rq.cli import cli as rq_cli
from rq.defaults import DEFAULT_RESULT_TTL, DEFAULT_WORKER_TTL


try:
    from flask.cli import AppGroup, ScriptInfo
except ImportError:  # pragma: no cover
    try:
        from flask_cli import AppGroup, ScriptInfo
    except ImportError:
        raise RuntimeError('Cannot import Flask CLI. Is it installed?')

try:
    from rq_scheduler import Scheduler
    from rq_scheduler.utils import setup_loghandlers
except ImportError:  # pragma: no cover
    Scheduler = None

_commands = {}


def shared_options(rq):
    "Default class options to pass to the CLI commands."
    return {
        'url': rq.redis_url,
        'config': None,
        'worker_class': rq.worker_class,
        'job_class': rq.job_class,
        'queue_class': rq.queue_class,
        'connection_class': rq.connection_class,
    }


def rq_command(condition=True):
    def wrapper(func):
        """Marks a callback as wanting to receive the RQ object we've added
        to the context
        """
        @click.pass_context
        def new_func(ctx, *args, **kwargs):
            rq = ctx.obj.data.get('rq')
            return func(rq, ctx, *args, **kwargs)
        updated_wrapper = update_wrapper(new_func, func)
        if condition:
            _commands[updated_wrapper.__name__] = updated_wrapper
        return updated_wrapper
    return wrapper


@click.option('--all', '-a', is_flag=True, help='Empty all queues')
@click.argument('queues', nargs=-1)
@rq_command()
def empty(rq, ctx, all, queues):
    "Empty given queues."
    return ctx.invoke(
        rq_cli.empty,
        all=all,
        queues=queues or rq.queues,
        **shared_options(rq)
    )


@click.option('--all', '-a', is_flag=True, help='Requeue all failed jobs')
@click.argument('job_ids', nargs=-1)
@rq_command()
def requeue(rq, ctx, all, job_ids):
    "Requeue failed jobs."
    return ctx.invoke(
        rq_cli.requeue,
        all=all,
        job_ids=job_ids,
        **shared_options(rq)
    )


@click.option('--path', '-P', default='.', help='Specify the import path.')
@click.option('--interval', '-i', type=float,
              help='Updates stats every N seconds (default: don\'t poll)')
@click.option('--raw', '-r', is_flag=True,
              help='Print only the raw numbers, no bar charts')
@click.option('--only-queues', '-Q', is_flag=True, help='Show only queue info')
@click.option('--only-workers', '-W', is_flag=True,
              help='Show only worker info')
@click.option('--by-queue', '-R', is_flag=True, help='Shows workers by queue')
@click.argument('queues', nargs=-1)
@rq_command()
def info(rq, ctx, path, interval, raw, only_queues, only_workers, by_queue,
         queues):
    "RQ command-line monitor."
    return ctx.invoke(
        rq_cli.info,
        path=path,
        interval=interval,
        raw=raw,
        only_queues=only_queues,
        only_workers=only_workers,
        by_queue=by_queue,
        queues=queues or rq.queues,
        **shared_options(rq)
    )


@click.option('--burst', '-b', is_flag=True,
              help='Run in burst mode (quit after all work is done)')
@click.option('--logging_level', type=str, default="INFO",
              help='Set logging level')
@click.option('--name', '-n', help='Specify a different name')
@click.option('--path', '-P', default='.', help='Specify the import path.')
@click.option('--results-ttl', type=int, default=DEFAULT_RESULT_TTL,
              help='Default results timeout to be used')
@click.option('--worker-ttl', type=int, default=DEFAULT_WORKER_TTL,
              help='Default worker timeout to be used (default: 420)')
@click.option('--verbose', '-v', is_flag=True, help='Show more output')
@click.option('--quiet', '-q', is_flag=True, help='Show less output')
@click.option('--sentry-dsn', default=None, help='Sentry DSN address')
@click.option('--exception-handler', help='Exception handler(s) to use',
              multiple=True)
@click.option('--pid',
              help='Write the process ID number to a file at '
                   'the specified path')
@click.argument('queues', nargs=-1)
@rq_command()
def worker(rq, ctx, burst, logging_level, name, path, results_ttl,
           worker_ttl, verbose, quiet, sentry_dsn, exception_handler, pid,
           queues):
    "Starts an RQ worker."
    ctx.invoke(
        rq_cli.worker,
        burst=burst,
        logging_level=logging_level,
        name=name,
        path=path,
        results_ttl=results_ttl,
        worker_ttl=worker_ttl,
        verbose=verbose,
        quiet=quiet,
        sentry_dsn=sentry_dsn,
        exception_handler=exception_handler or rq._exception_handlers,
        pid=pid,
        queues=queues or rq.queues,
        **shared_options(rq)
    )


@rq_command()
@click.option('--duration', type=int,
              help='Seconds you want the workers to be suspended. '
                   'Default is forever.')
def suspend(rq, ctx, duration):
    "Suspends all workers."
    ctx.invoke(
        rq_cli.suspend,
        duration=duration,
        **shared_options(rq)
    )


@rq_command()
def resume(rq, ctx):
    "Resumes all workers."
    ctx.invoke(
        rq_cli.resume,
        **shared_options(rq)
    )


@click.option('--verbose', '-v', is_flag=True, help='Show more output')
@click.option('--burst', '-b', is_flag=True,
              help='Run in burst mode (quit after all work is done)')
@click.option('-q', '--queue', metavar='QUEUE',
              help='The name of the queue to run the scheduler with.')
@click.option('-i', '--interval', metavar='SECONDS', type=int,
              help='How often the scheduler checks for new jobs to add to '
                   'the queue (in seconds, can be floating-point for more '
                   'precision).')
@click.option('--pid', metavar='FILE',
              help='Write the process ID number '
                   'to a file at the specified path')
@rq_command(Scheduler is not None)
def scheduler(rq, ctx, verbose, burst, queue, interval, pid):
    "Periodically checks for scheduled jobs."
    scheduler = rq.get_scheduler(interval=interval, queue=queue)
    if pid:
        with open(os.path.expanduser(pid), 'w') as fp:
            fp.write(str(os.getpid()))
    if verbose:
        level = 'DEBUG'
    else:
        level = 'INFO'
    setup_loghandlers(level)
    scheduler.run(burst=burst)


def add_commands(cli, rq):
    @click.group(cls=AppGroup, help='Runs RQ commands with app context.')
    @click.pass_context
    def rq_group(ctx):
        ctx.ensure_object(ScriptInfo).data['rq'] = rq

    sorted_commands = sorted(_commands.items(), key=operator.itemgetter(0))
    for name, func in sorted_commands:
        rq_group.command(name=name)(func)

    cli.add_command(rq_group, name='rq')
