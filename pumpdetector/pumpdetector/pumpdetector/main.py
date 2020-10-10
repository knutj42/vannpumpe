import datetime
import os

import requests
import time
import logging

logger = logging.getLogger(__name__)

timestamp_format = "%Y/%m/%d %H:%M:%S Z"
elasticsearch_timestamp_format = "yyyy/MM/dd HH:mm:ss Z"

import pytz

local_tz = pytz.timezone('Europe/Oslo')


def parse_timestamp(timestamp_string):
    tm = datetime.datetime.strptime(timestamp_string, timestamp_format)
    tm = tm.replace(tzinfo=datetime.timezone.utc).astimezone(tz=local_tz)
    return tm


def format_timestamp(timestamp):
    timestamp_string = timestamp.astimezone(datetime.timezone.utc).strftime(timestamp_format)
    return timestamp_string


pump_run_water_level_limit = int(os.environ.get("PUMP_RUN_WATER_LEVEL_LIMIT", "15"))


def main(elasticsearch_base_url):
    # First, read the last entry from the "pumprun" elasticsearch index. We need this to know where to start reading
    # from the "vannpumpe" index.
    logger.info("Pumpdetector starting up.")
    if not elasticsearch_base_url.endswith("/"):
        elasticsearch_base_url += "/"

    pumpdetector_url = elasticsearch_base_url + "pumpdetector"

    pumpdetector_day_total_url = elasticsearch_base_url + "pumpdetector_day_total"
    if requests.get(pumpdetector_day_total_url).status_code == 404:
        response = requests.put(pumpdetector_day_total_url, json={
            "mappings": {
                "log": {
                    "dynamic_date_formats": [elasticsearch_timestamp_format]
                }
            }
        })
        if response.status_code != 200:
            raise AssertionError(
                f"Failed to create the 'pumpdetector' index! "
                f"response.status_code: ${response.status_code}  response.text:${response.text}")

    #requests.delete(pumpdetector_url)
    response = requests.get(pumpdetector_url + "/_search", json=
    {
        "query": {
            "match_all": {}
        },
        "size": 1,
        "sort": [
            {
                "@timestamp": {
                    "unmapped_type": "date",
                    "order": "desc"
                }
            }
        ]
    })

    if response.status_code == 200:
        result = response.json()
        if result["_shards"]["failed"] != 0 or result["_shards"]["successful"] == 0:
            raise AssertionError(f"Failed to get the latest entry from the 'pumpdetector' index! result:${result}")

        hits = result["hits"]["hits"]

    elif response.status_code == 404:
        response = requests.put(pumpdetector_url, json={
            "mappings": {
                "log": {
                    "dynamic_date_formats": [elasticsearch_timestamp_format]
                }
            }
        })
        if response.status_code != 200:
            raise AssertionError(
                f"Failed to create the 'pumpdetector' index! "
                f"response.status_code: ${response.status_code}  response.text:${response.text}")
        hits = []

    else:
        raise AssertionError(
            f"Failed to get the latest entry from the 'pumpdetector' index! "
            f"response.status_code: ${response.status_code}  response.text:${response.text}")

    if hits:
        last_timestamp = hits[0]["_source"]["@timestamp"]
    else:
        last_timestamp = datetime.datetime(year=2018, month=1, day=1).strftime(timestamp_format)
    last_pump_started_timestamp = parse_timestamp(last_timestamp)

    vannpumpe_search_url = elasticsearch_base_url + "vannpumpe/_search"

    min_water_level = 9999
    max_water_level = 0
    min_water_level_timestamp = None
    max_water_level_timestamp = None
    is_waiting_for_the_value_to_start_rising = False

    previous_timestamp = parse_timestamp(last_timestamp)

    while True:
        response = requests.get(vannpumpe_search_url, json=
        {
            "query": {
                "range": {
                    "@timestamp": {
                        "gt": last_timestamp,
                    }
                }
            },
            "size": 100,
            "sort": [
                {
                    "@timestamp": {
                        "order": "asc"
                    }
                }
            ]
        })
        if response.status_code != 200:
            raise AssertionError(
                f"Failed to get new entries from the 'vannpumpe' index! "
                f"response.status_code: ${response.status_code}  response.text:${response.text}")

        result = response.json()
        if result["_shards"]["failed"] != 0 or result["_shards"]["successful"] == 0:
            raise AssertionError(f"Failed to get the latest entry from the 'pumpdetector' index! result:${result}")

        hits = result["hits"]["hits"]
        if hits:
            last_timestamp = hits[-1]["_source"]["@timestamp"]
        else:
            time.sleep(60)

        for hit in hits:
            source = hit["_source"]
            water_level = source["water-level"]
            timestamp = parse_timestamp(source["@timestamp"])
            if timestamp <= previous_timestamp:
                logger.warning(f"The timestamp ${timestamp} wasn't larger than the previous timestamp ${previous_timestamp}! I'll ignore this hit: %s", hit)
                continue

            previous_timestamp = timestamp

            if not is_waiting_for_the_value_to_start_rising:
                # we must wait until the water_level dips below (max_water_level - pump_run_water_level_limit).
                diff = (max_water_level - water_level)
                if diff > pump_run_water_level_limit:
                    is_waiting_for_the_value_to_start_rising = True
                    min_water_level_timestamp = timestamp
                    min_water_level = water_level
                else:
                    if water_level > max_water_level:
                        max_water_level = water_level
                        max_water_level_timestamp = timestamp
                    else:
                        seconds_since_max_value = (timestamp - max_water_level_timestamp).total_seconds()
                        if seconds_since_max_value > 1800:
                            # a pipe-run never takes this long, so something is wrong. We reset all state.
                            max_water_level = water_level
                            min_water_level = water_level
                            max_water_level_timestamp = timestamp
                            min_water_level_timestamp = timestamp


            else:
                if water_level < min_water_level:
                    min_water_level_timestamp = timestamp
                    min_water_level = water_level

                elif water_level > min_water_level:
                    # ok, the value has started to rise again, so we have found the lowest water-level for this
                    # pump-run.

                    assert min_water_level_timestamp > max_water_level_timestamp
                    assert min_water_level < max_water_level

                    pump_started_event = {
                        "@timestamp": format_timestamp(min_water_level_timestamp),
                        "max_water_level": max_water_level,
                        "max_water_level_timestamp": format_timestamp(max_water_level_timestamp),
                        "min_water_level": min_water_level,
                        "min_water_level_timestamp": format_timestamp(min_water_level_timestamp),
                        "water_level_diff": max_water_level - min_water_level,
                    }

                    logger.info(
                        "Found a pump-started-event in the timerange %s => %s (%.0f seconds after the last event). water-level: %s => %s.  pump_started_event:%s",
                        max_water_level_timestamp, min_water_level_timestamp,
                        (min_water_level_timestamp - last_pump_started_timestamp).total_seconds(),
                        max_water_level, min_water_level,
                        pump_started_event,
                        )

                    response = requests.post(pumpdetector_url + "/log", json=pump_started_event)
                    if response.status_code != 201:
                        raise AssertionError(
                            "Failed to store the log-item in elasticsearch! response.status_code:%s  response.text:%s" % (
                                response.status_code, response.text))

                    last_pump_started_timestamp = min_water_level_timestamp
                    is_waiting_for_the_value_to_start_rising = False
                    max_water_level = 0
                    min_water_level = 9999
                    max_water_level_timestamp = None
                    min_water_level_timestamp = None
