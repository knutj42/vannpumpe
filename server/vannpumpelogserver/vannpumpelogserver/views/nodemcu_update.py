import logging
import os

import flask
from vannpumpelogserver import app
from werkzeug.exceptions import BadRequest

logger = logging.getLogger(__name__)


@app.route('/nodemcu_update', methods=["GET"])
def nodemcu_update():
    current_version = flask.request.headers.get("X_ESP8266_VERSION")

    try:
        current_version = int(current_version)
    except (ValueError, TypeError):
        raise BadRequest("The 'X_ESP8266_VERSION' header should contain an integer")

    latest_version, latest_version_filepath = get_latest_firmware()
    if current_version >= latest_version:
        return "you are up-to-date", 304
    else:
        logger.info("nodemcu_update() updating client from version %s to %s" % (
            current_version, latest_version
        ))
        return flask.send_file(latest_version_filepath,
                                   mimetype="application/octet-stream",
                                   as_attachment=True)


def get_latest_firmware():
    nodemcu_firmware_folder = os.environ["VANNPUMPE_NODEMCU_FIRMWARE_FOLDER"]
    nodemcu_firmware_prefix = "nodemcu.bin.ver"
    max_file_version = 0
    max_file_version_filepath = None
    for dir_entry in os.scandir(nodemcu_firmware_folder):
        name = dir_entry.name
        if name.startswith(nodemcu_firmware_prefix):
            file_version =  int(name[len(nodemcu_firmware_prefix):])
            if file_version > max_file_version:
                max_file_version = file_version
                max_file_version_filepath = dir_entry.path

    return max_file_version, max_file_version_filepath
