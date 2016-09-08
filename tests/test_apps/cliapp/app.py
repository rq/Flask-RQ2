from __future__ import absolute_import, print_function

from flask import Flask
from flask_cli import FlaskCLI

testapp = Flask('testapp')
FlaskCLI(testapp)
