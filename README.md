# Sunjobs

Run a daily kubernetes cronjob that creates and manages a sunrise and sunset kubernetes cronjob for the day by leveraging OpenWeatherMap's API.

For example, you can use this to make a RESTful call to turn a smart bulb on and off at sunset and sunrise.

# Prerequisites

A kubernetes environment such as microk8s.

# Usage

#### Clone this repository:

```bash
git clone https://github.com/kennedn/subjobs
cd sunjobs
```

#### Create a config/variables.py file:

```bash
mkdir config
vi config/variables.py
```

Required variables in variables.py are as follows:

|Variables        |Description|
|-----------------|------------------------------------------------------------------|
|OPENWEATHERMAP_API_KEY| API key for OpenWeatherMaps|
|LATITUDE | Latitude to sample sunrise / sunset times at|
|LONGITUDE | Longitude to sample sunrise / sunset times at|
|CONTAINER_IMAGE | Container image to use for sunrise / sunset commands|
|SUNRISE_COMMAND | Command to run at sunrise|
|SUNSET_COMMAND  | Command to run at sunset|

Example:

```python
!/usr/bin/env python3
# Your OpenWeatherMap API key
OPENWEATHERMAP_API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Define location
LATITUDE = 51.550
LONGITUDE = -0.110

# Container commands
CONTAINER_IMAGE = "curlimages/curl"
SUNRISE_COMMAND = ["curl", "-X", "PUT", "https://cool.api/v1/meross/sad_light?code=toggle&value=0"]
SUNSET_COMMAND = ["curl", "-X", "PUT", "https://cool.api/v1/meross/sad_light?code=toggle&value=1"]
```

#### Apply the cronjob and variables.py to the cluster
```bash
kubectl apply -k .
```

#### Optional: Manually trigger the job and ensure sunrise and sunset cronjobs appear
```bash 
kubectl create job --from=cronjob/sunjobs test-sunjobs
```

```bash
kubectl logs jobs/test-sunjobs
```

output:
```bash
❯ kubectl logs jobs/test-sunjobs
2023-10-21 10:49:35,479 - INFO - Retrieved sunrise time: 2023-10-21 07:55:17+01:00
2023-10-21 10:49:35,479 - INFO - Retrieved sunset time: 2023-10-21 17:59:52+01:00
2023-10-21 10:49:35,501 - INFO - sunrise-job job updated
2023-10-21 10:49:35,531 - INFO - sunset-job job created
```

```bash
kubectl get cronjobs
```

output:
```bash
❯ kubectl get cronjobs
NAME                      SCHEDULE      SUSPEND   ACTIVE   LAST SCHEDULE   AGE
sunjobs                   0 0 * * *     False     0        12h             40h
sunrise-job               45 07 * * *   False     0        4h24m           41h
sunset-job                49 17 * * *   False     0        <none>          17m
```






