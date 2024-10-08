import requests
import logging
from pytz import UTC, timezone
from kubernetes import client, config
from datetime import datetime, timedelta
from variables import OPENWEATHERMAP_API_KEY, LATITUDE, LONGITUDE, TIMEZONE, CONTAINER_IMAGE, SUNRISE_COMMAND, SUNSET_COMMAND, OFFSET_MINUTES

# Define the base URL for OpenWeatherMap API
OPENWEATHERMAP_URL = "http://api.openweathermap.org/data/2.5"

# Define the API endpoint for sunrise and sunset times
SUNRISE_SUNSET_ENDPOINT = "/weather"

# Kubernetes Job template for the curl command
JOB_TEMPLATE = {
    "apiVersion": "batch/v1",
    "kind": "Job",
    "metadata": {"name": ""},
    "spec": {
        "template": {
            "spec": {
                "containers": [
                    {
                        "name": "curl-job",
                        "image": CONTAINER_IMAGE,
                        "command": [],
                    }
                ],
                "restartPolicy": "OnFailure",
            }
        }
    }
}

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger()

def get_sunrise_sunset_times():
    params = {
        "lat": LATITUDE,
        "lon": LONGITUDE,
        "appid": OPENWEATHERMAP_API_KEY
    }
    response = requests.get(f"{OPENWEATHERMAP_URL}{SUNRISE_SUNSET_ENDPOINT}", params=params)
    data = response.json()
    sunrise_timestamp = data["sys"]["sunrise"]
    sunset_timestamp = data["sys"]["sunset"]
    sunrise_time = datetime.utcfromtimestamp(sunrise_timestamp).replace(tzinfo=UTC).astimezone(timezone(TIMEZONE))
    sunset_time = datetime.utcfromtimestamp(sunset_timestamp).replace(tzinfo=UTC).astimezone(timezone(TIMEZONE))
    return sunrise_time, sunset_time

def create_or_update_kubernetes_job(name, schedule_time, sunrise):
    job = JOB_TEMPLATE.copy()
    job["metadata"]["name"] = name
    if sunrise:
        job["spec"]["template"]["spec"]["containers"][0]["command"] = SUNRISE_COMMAND
    else:
        job["spec"]["template"]["spec"]["containers"][0]["command"] = SUNSET_COMMAND

    job_schedule = (schedule_time - timedelta(minutes=OFFSET_MINUTES)).strftime("%M %H * * *")
    cron_job = client.V1CronJob(
        metadata=client.V1ObjectMeta(name=name),
        spec=client.V1CronJobSpec(
            schedule=job_schedule,
            job_template=client.V1JobTemplateSpec(
                spec=client.V1JobSpec(template=job["spec"]["template"])
            ),
        ),
    )
    api_instance = client.BatchV1Api()
    
    try:
        existing_cron_job = api_instance.read_namespaced_cron_job(name=name, namespace="default")
        existing_cron_job.spec.schedule = cron_job.spec.schedule
        api_instance.delete_namespaced_cron_job(name=name, namespace="default")
        api_instance.create_namespaced_cron_job(namespace="default", body=cron_job)
        logger.info(f"{name} job created with cron schedule {job_schedule}")
    except client.rest.ApiException as e:
        if e.status == 404:
            api_instance.create_namespaced_cron_job(namespace="default", body=cron_job)
            return
        logger.error(f"Error: {e}")
        raise Exception("Unable to create cronjob")

def main():
    try:
        config.load_incluster_config()
    except config.ConfigException:
        try:
            config.load_kube_config()
        except config.ConfigException:
            raise Exception("Could not configure kubernetes python client")


    sunrise_time, sunset_time = get_sunrise_sunset_times()
    logger.info(f"Retrieved sunrise time: {sunrise_time}")
    logger.info(f"Retrieved sunset time: {sunset_time}")

    create_or_update_kubernetes_job("sunrise-job", sunrise_time, True)
    create_or_update_kubernetes_job("sunset-job", sunset_time, False)

if __name__ == "__main__":
    main()

