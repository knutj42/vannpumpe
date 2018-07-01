import logging
import pprint
import textwrap

import docker

import flask
import requests
from vannpumpelogserver import app


logger = logging.getLogger(__name__)

docker_client = docker.from_env()


@app.route('/health_check', methods=["GET"])
def health_check():
    errors = []

    ###################################################################
    # Check that all the required docker containers are running
    ###################################################################
    required_containers = {
        "grafana",
        "elasticsearch",
        "nginx",
        "vannpumpelogserver",
    }
    running_containers = set()
    for container in docker_client.containers.list():
        #logger.info("container.attrs for the container '%s': %s" % (container.name,
        #                                                            pprint.pformat(container.attrs)))
        if container.attrs["State"]["Status"] == "running":
            container_name = container.name
            container_name = container_name.replace("knutj_", "")
            container_name = container_name.replace("_1", "")
            running_containers.add(container_name)

    #logger.info("running_containers: %s" % (running_containers,))

    missing_containers = required_containers - running_containers
    if missing_containers:
        for container_name in missing_containers:
            errors.append("The docker-container '%s' is not running!" % (container_name,))

    ###################################################################
    # Check if any grafana alerts have triggered.
    ###################################################################
    try:
        response = requests.get("http://grafana:3000/api/alerts?dashboardId=vannpumpe-alerts", timeout=30)
        if response.status_code == 200:
            alerts = response.json()
            for alert in alerts:
                if alert["state"] != "ok":
                    errors.append("The grafana alert '%s' is not ok:\n%s" % (
                        alert["name"],
                        textwrap.indent(pprint.pformat(alert), prefix="      ")
                    ))
        else:
            errors.append("Grafana returned a %s-response! response.text:%s" % (response.status_code,
                                                                                response.text,))

    except requests.RequestException as e:
        errors.append("Failed to talk to grafana! error: %s" % (e,))

    if not errors:
        return "All is well."
    else:
        response = flask.Response("Something is wrong!\n    %s" % ("\n    ".join(errors, )),
                                  status=503,
                                  mimetype="text/plain")
        return response
