import logging
import os
import os.path

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)-12s %(threadName)-10s %(levelname)-8s %(message)s')
logging.getLogger("googleapiclient.discovery").setLevel(logging.WARNING)
logging.getLogger("werkzeug").setLevel(logging.WARNING)

from vannpumpelogserver import app

logger = logging.getLogger(__name__)


def main():
    authorization_token = os.environ.get("VANNPUMPE_AUTHORIZATION_TOKEN")
    if not authorization_token:
        raise AssertionError("No 'VANNPUMPE_AUTHORIZATION_TOKEN' environment variable was specified!")

    app.config["AUTHORIZATION_TOKEN"] = authorization_token

    host = "0.0.0.0"
    port = 17000
    logger.info("Starting webserver at http://%s:%s" % (host, port))
    app.run(host=host, port=port)


if __name__ == '__main__':
    main()
