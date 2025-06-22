import os, sys, pytest

# Ensure magenta-api folder is on path
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'magenta-api'))
sys.path.insert(0, ROOT)

import app as flask_app_module  # noqa

@pytest.fixture
def client():
    flask_app_module.app.testing = True
    return flask_app_module.app.test_client()
