import logging
import pprint

import flask
from vannpumpelogserver import app, store
from werkzeug.exceptions import Unauthorized, Forbidden

logger = logging.getLogger(__name__)


@app.route('/')
def index():
    return flask.render_template("index.html")


@app.route('/log', methods=["POST"])
def add_log_entry():
    required_auth_tokens = app.config["AUTHORIZATION_TOKEN"].split(",")
    auth_token = flask.request.headers.get("AUTHORIZATION")
    if not auth_token:
        logger.warning("/log was called without an AUTHORIZATION header")
        raise Unauthorized()

    if auth_token not in required_auth_tokens:
        logger.warning("/log was called with an invalid AUTHORIZATION header")
        raise Forbidden()

    log_entry = flask.request.json
    logger.info("Got a log entry: %s", pprint.pformat(log_entry))

    store.append(log_entry)

    return "ok"
