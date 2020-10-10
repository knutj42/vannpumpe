import datetime
import logging
import os
import urllib.parse
import requests
import flask

logger = logging.getLogger(__name__)


app = flask.Flask(__name__)

class ElasticssearchStore:
    """This is the class that encapsulates the persistent store that the readings are
    stored in.

    This implementation posts the readings to an elasticsearch database.
    """

    def __init__(self):
        elasticsearch_url = os.environ.get("VANNPUMPE_ELASTICSEARCH_URL")
        if not elasticsearch_url:
            raise AssertionError("No 'VANNPUMPE_ELASTICSEARCH_URL' environment variable was specified!")
        self._elasticsearch_post_url = urllib.parse.urljoin(elasticsearch_url, "vannpumpe/log")

    def append(self, reading):
        currenttime = datetime.datetime.utcnow()
        # Elasticsearch expects datetimes to be on the format "yyyy/MM/dd HH:mm:ss Z", and the
        # default timestamp-field is "@timestamp".
        reading["@timestamp"] = currenttime.strftime("%Y/%m/%d %H:%M:%S Z")
        response = requests.post(self._elasticsearch_post_url, json=reading)
        if response.status_code != 201:
            logger.error(
                "Failed to store the log-item in elasticsearch! response.status_code:%s  response.text:%s" % (
                    response.status_code, response.text))


store = ElasticssearchStore()

# noinspection PyUnresolvedReferences
import vannpumpelogserver.views  # this import is required to register the flask views.

