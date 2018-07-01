import collections
import logging
import os
import threading
import urllib.parse
import requests

import datetime
import oauth2client.service_account
import apiclient.discovery
import flask

logger = logging.getLogger(__name__)

app = flask.Flask(__name__)

app.config['SECRET_KEY'] = 'jlaf098348ym|1jdå01caa-!'


class Store:
    """This is the class that encapsulates the persistent store that the readings are
    stored in.

    This implementation appends the readings to a Google sheet and to a elasticsearch database.
    """

    def __init__(self):
        self._column_lock = threading.RLock()

        elasticsearch_url = os.environ.get("VANNPUMPE_ELASTICSEARCH_URL")
        if not elasticsearch_url:
            raise AssertionError("No 'VANNPUMPE_ELASTICSEARCH_URL' environment variable was specified!")

        self._elasticsearch_post_url = urllib.parse.urljoin(elasticsearch_url, "vannpumpe/log")

        keyfilename = os.environ.get("VANNPUMPE_GOOGLE_SERVICE_ACCOUNT_KEYFILE")
        if not keyfilename:
            raise AssertionError("No 'VANNPUMPE_GOOGLE_SERVICE_ACCOUNT_KEYFILE' environment variable was specified!")
        if not os.path.exists(keyfilename):
            raise AssertionError("The file '%s' doesn't exist!" % (keyfilename,))

        self._spreadsheetId = os.environ.get("VANNPUMPE_SPREADSHEET_ID")
        if not self._spreadsheetId:
            raise AssertionError("No 'VANNPUMPE_SPREADSHEET_ID' environment variable was specified!")

        credentials = oauth2client.service_account.ServiceAccountCredentials.from_json_keyfile_name(keyfilename)

        self._service = apiclient.discovery.build("sheets", "v4", credentials=credentials,
                                                  cache_discovery=False)

        result = self._service.spreadsheets().values().get(spreadsheetId=self._spreadsheetId,
                                                           range="Sheet1!A1:Z1").execute()

        if "values" in result:
            columns = result["values"][0]
        else:
            columns = []
        self.columnname2index = collections.OrderedDict((columnname, index) for index, columnname in enumerate(columns))

        for column in ["timestamp", "pump-running"]:
            if column not in self.columnname2index:
                self._add_column(column)

    def _add_column(self, columnname):
        with self._column_lock:
            assert columnname not in self.columnname2index
            index = len(self.columnname2index)
            self.columnname2index[columnname] = index
            columns = list(self.columnname2index.keys())

            self._service.spreadsheets().values().update(spreadsheetId=self._spreadsheetId,
                                                         range="Sheet1!A1:Z1",
                                                         valueInputOption="USER_ENTERED",
                                                         body={
                                                             "values": [
                                                                 columns
                                                             ],
                                                         }).execute()
            logger.info("Added a new column: '%s'" % (columnname,))

    def append(self, reading):
        currenttime = datetime.datetime.utcnow()
        reading["timestamp"] = currenttime.isoformat(sep=" ")

        # check if we must update the colums in the spreadsheet
        values_with_indexes = []
        for column_name, value in reading.items():
            index = self.columnname2index.get(column_name)
            if index is None:
                index = self._add_column(column_name)
            values_with_indexes.append((index, value))

        values = []
        for column_name in self.columnname2index.keys():
            value = reading.get(column_name)
            values.append(value)

        self._service.spreadsheets().values().append(spreadsheetId=self._spreadsheetId,
                                                     range="Sheet1",
                                                     valueInputOption="USER_ENTERED",
                                                     body={
                                                         "values": [
                                                             values
                                                         ],
                                                     }).execute()

        # Elasticsearch expects datetimes to be on the format "yyyy/MM/dd HH:mm:ss Z", and the
        # default timestamp-field is "@timestamp".
        del reading["timestamp"]
        reading["@timestamp"] = currenttime.strftime("%Y/%m/%d %H:%M:%S Z")

        response = requests.post(self._elasticsearch_post_url, json=reading)
        if response.status_code != 201:
            logger.error(
                "Failed to store the log-item in elasticsearch! response.status_code:%s  response.text:%s" % (
                    response.status_code, response.text))

store = Store()

import vannpumpelogserver.views
