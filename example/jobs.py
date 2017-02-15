from flask_rq2 import RQ

rq = RQ()


@rq.job
def calculate(x, y):
    return x + y
