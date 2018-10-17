import logging
import os
import os.path

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)-12s %(threadName)-10s %(levelname)-8s %(message)s')

import pumpdetector.main

logger = logging.getLogger(__name__)


def main():
    elasticsearch_base_url = os.environ.get("VANNPUMPE_ELASTICSEARCH_URL")
    if not elasticsearch_base_url:
        raise AssertionError("No 'VANNPUMPE_ELASTICSEARCH_URL' environment variable was specified!")

    pumpdetector.main.main(elasticsearch_base_url)

if __name__ == '__main__':
    main()
