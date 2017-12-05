from flask_rq2.job import FlaskJob


def add(x, y):
    return x + y


def test_app_loading(test_apps, monkeypatch):
    monkeypatch.setenv('FLASK_APP', 'rqapp.app:testapp')

    from rqapp.app import testrq

    job = FlaskJob(connection=testrq.connection)

    assert job.load_app()
