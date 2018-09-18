import uuid
from datetime import datetime, timedelta

from rq.utils import import_attribute

from flask_rq2 import RQ
from flask_rq2.functions import JobFunctions


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


def test_job_with_valid_params(rq):

    @rq.job(timeout=1337, result_ttl=1984, ttl=666)
    def subtract(x, y):
        return x - y

    assert subtract.helper.queue_name == rq.default_queue
    assert subtract.helper.timeout == 1337
    assert subtract.helper.result_ttl == 1984
    assert subtract.helper.ttl == 666


def test_job_with_fallback_params(rq):

    @rq.job('', result_ttl=0)
    def subtract(x, y):
        return x - y

    assert subtract.helper.queue_name == rq.default_queue
    assert subtract.helper.result_ttl == 0 != rq.default_result_ttl


def add(x, y):
    return x + y


def test_queue_job(app):
    rq = RQ(app, is_async=True)
    rq.connection.flushdb()
    rq.job(add)

    job1 = add.queue(1, 2)
    assert isinstance(job1, import_attribute(rq.job_class))
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

    other_queue = 'other_queue'
    job5 = add.queue(9, 10, queue=other_queue)
    # job will be scheduled in the other queue eventually
    assert job5.origin == other_queue

    job6 = add.queue(11, 12)
    result = job6.perform()
    assert result == 23

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


def test_job_override(app, config):
    rq = RQ(app, is_async=True)

    rq.job(add, timeout=123, result_ttl=456, ttl=789)
    assert add.helper.timeout == 123
    assert add.helper.result_ttl == 456
    assert add.helper.ttl == 789

    job1 = add.queue(timeout=111, result_ttl=222, ttl=333)
    assert job1.timeout == 111
    assert job1.result_ttl == 222
    assert job1.ttl == 333


def test_factory_pattern(app, config):
    rq = RQ(default_timeout=111)
    rq.init_app(app)

    # override some rq defaults
    rq.default_timeout = 222
    rq.default_result_ttl = 333
    rq.default_queue = 'non-default'
    rq.job(add)

    # then check if those default have been passed to the helper
    assert add.helper.timeout == 222
    assert add.helper.result_ttl == 333
    assert add.helper.queue_name == 'non-default'

    # then queue if the values have been passed to the job as well
    job = add.queue(1, 2)
    assert job.timeout == 222
    assert job.result_ttl == 333
    assert job.ttl is None
    assert job.origin == 'non-default'

    # change the values in the helpr and see if that works
    add.helper.timeout = 444
    assert add.helper.timeout == 444
    add.helper.result_ttl = 555
    assert add.helper.result_ttl == 555
    add.helper.queue_name = 'totally-different'
    assert add.helper.queue_name == 'totally-different'

    # assert the helper's values
    job = add.queue(1, 2)
    assert job.timeout == 444
    assert job.result_ttl == 555
    assert job.ttl is None
    assert job.origin == 'totally-different'

    # now finally override the values while queueing
    job = add.queue(1, 2,
                    queue='yet-another', timeout=666, result_ttl=777, ttl=888)
    assert job.timeout == 666
    assert job.result_ttl == 777
    assert job.ttl == 888
    assert job.origin == 'yet-another'


def purge(scheduler):
    [scheduler.cancel(job) for job in scheduler.get_jobs()]


def test_schedule_job(app):
    rq = RQ(app, is_async=True)
    scheduler = rq.get_scheduler()
    purge(scheduler)
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

    other_queue = 'other-queue'
    job4 = add.schedule(timedelta(seconds=1), 5, 6, queue=other_queue)
    # job will be scheduled in the other queue eventually
    assert job4.origin == other_queue
    # one more. the scheduler will have all jobs, no matter what
    # queue the job will eventually be queued in.
    assert job4 in scheduler.get_jobs()
    purge(scheduler)


def test_cron_job(app):
    rq = RQ(app, is_async=True)
    scheduler = rq.get_scheduler()
    purge(scheduler)
    assert scheduler.count() == 0
    rq.job(add)

    cron_string = '* * * * *'
    cron_name = 'add-it-for-real'
    job1 = add.cron(cron_string, cron_name, 1, 2)
    assert scheduler.count() == 1
    assert job1 in scheduler.get_jobs()
    assert job1.meta['cron_string'] == cron_string
    assert job1.id == 'cron-' + cron_name
    purge(scheduler)

    job2 = add.cron(cron_string, cron_name, 3, 4)
    assert scheduler.count() == 1  # no duplicate here
    assert job2 in scheduler.get_jobs()
    assert job2.meta['cron_string'] == cron_string
    assert job2.id == 'cron-' + cron_name

    job3 = add.cron(cron_string, cron_name + '-pro', 3, 4)
    assert scheduler.count() == 2  # second cron
    assert job3 in scheduler.get_jobs()
    assert job3.id == 'cron-' + cron_name + '-pro'

    other_queue = 'other-queue'
    job4 = add.cron(cron_string, cron_name + '-other', 3, 4, queue=other_queue)
    # job will be scheduled in the other queue eventually
    assert job4.origin == other_queue
    # one more. the scheduler will have all jobs, no matter what
    # queue the job will eventually be queued in.
    assert job4 in scheduler.get_jobs()
    assert scheduler.count() == 3

    purge(scheduler)
