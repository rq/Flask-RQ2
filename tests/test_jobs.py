import uuid
from datetime import datetime, timedelta

from flask_rq2 import RQ
from flask_rq2.helpers import JobFunctions


def test_job(rq):
    @rq.job
    def add(x, y):
        return x + y

    assert rq._jobs == [add]
    assert isinstance(add.helper, JobFunctions)
    assert add.helper.queue_name == rq.default_queue
    assert repr(add.helper) == '<JobFunctions %s.add>' % __name__

    @rq.job()
    def multiply(x, y):
        return x * y

    assert multiply.helper.queue_name == rq.default_queue


def test_job_custom_queue(rq):

    @rq.job('non-default')
    def add(x, y):
        return x + y

    assert rq._jobs == [add]
    assert isinstance(add.helper, JobFunctions)
    assert add.helper.queue_name != rq.default_queue
    assert add.helper.queue_name == 'non-default'


def test_job_with_params(rq):

    @rq.job(timeout=1337, result_ttl=1984, ttl=666)
    def substract(x, y):
        return x - y

    assert substract.helper.queue_name == rq.default_queue
    assert substract.helper.timeout == 1337
    assert substract.helper.result_ttl == 1984
    assert substract.helper.ttl == 666


def add(x, y):
    return x + y


def test_queue_job(app):
    rq = RQ(app, async=True)

    rq.job(add)

    job1 = add.queue(1, 2)
    assert isinstance(job1, rq.job_cls)
    assert job1.args == (1, 2)
    assert job1.kwargs == {}
    assert job1.timeout == add.helper.timeout == rq.default_timeout

    job2 = add.queue(3, 4, description='job 2')
    assert job2.description == 'job 2'

    job3_id = uuid.uuid4().hex
    job3 = add.queue(5, 6, job_id=job3_id)
    assert job3.id == job3_id

    job4 = add.queue(7, 8, depends_on=job3)
    assert job4.dependency.id == job3.id

    job5 = add.queue(9, 10)
    result = job5.perform()
    assert result == 19

    queue = rq.get_queue()
    assert job1 in queue.jobs
    assert job2 in queue.jobs
    assert job3 in queue.jobs
    # job 4 is a dependency on job 3, so not queued yet
    assert job4 not in queue.jobs

    assert job3.result is None
    assert job4.result is None
    response = rq.get_worker('default').work(True)
    assert response
    assert job4.dependency.result == 11
    assert job4.result == 15

    assert len(queue.jobs) == 0


def purge(scheduler):
    [scheduler.cancel(job) for job in scheduler.get_jobs()]


def test_schedule_job(app):
    rq = RQ(app, async=True)
    scheduler = rq.get_scheduler()
    assert scheduler.count() == 0
    rq.job(add)

    job1 = add.schedule(timedelta(seconds=1), 1, 2)
    assert scheduler.count() == 1
    assert job1 in scheduler.get_jobs()
    purge(scheduler)

    job2 = add.schedule(datetime.utcnow() + timedelta(seconds=1), 3, 4)
    assert scheduler.count() == 1
    assert job2 in scheduler.get_jobs()
    purge(scheduler)

    job3_id = uuid.uuid4().hex
    job3_description = 'custom description'
    job3 = add.schedule(timedelta(seconds=1), 5, 6, repeat=10, interval=2,
                        description=job3_description, job_id=job3_id)
    assert job3 in scheduler.get_jobs()
    assert job3.meta.get('repeat') == 10
    assert job3.meta.get('interval') == 2
    assert job3.id == job3_id
    assert job3.description == job3_description
    purge(scheduler)


def test_cron_job(app):
    rq = RQ(app, async=True)
    scheduler = rq.get_scheduler()
    assert scheduler.count() == 0
    rq.job(add)

    cron_string = '* * * * *'
    cron_name = 'add-it-for-real'
    job1 = add.cron(cron_string, cron_name, 1, 2)
    assert scheduler.count() == 1
    assert job1 in scheduler.get_jobs()
    assert job1.meta['cron_string'] == cron_string
    assert job1.id == 'cron-' + cron_name
    # purge(scheduler)

    job2 = add.cron(cron_string, cron_name, 3, 4)
    assert scheduler.count() == 1  # no duplicate here
    assert job2 in scheduler.get_jobs()
    assert job2.meta['cron_string'] == cron_string
    assert job2.id == 'cron-' + cron_name

    job3 = add.cron(cron_string, cron_name + '-pro', 3, 4)
    assert scheduler.count() == 2  # second cron
    assert job3 in scheduler.get_jobs()
    assert job3.id == 'cron-' + cron_name + '-pro'

    purge(scheduler)
