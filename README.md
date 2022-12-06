# wetter-corona-daten

---

### Description

This Python program repeatedly gets current weather and corona data from the openweatherapp and RKI APIs, respectively.
The data is then stored in a user-specified InfluxDB database and can be used to build e.g. a Grafana dashboard from it.

### Setup and configuration

The easiest way to run this app is by creating a virtual environment in Python and install the dependencies from the file `requirements.txt`:

```
pip3 install virtualenv
python3 -m venv venv
source ./venv/bin/activate
pip3 install -r requirements.txt
```

Next, create a `.env` file and set the following variables:

```
VERSION=1.0
DB_USERNAME=<DATABASE USER>
DB_PASSWORD=<PASSWORD FOR DB USER>
DB_HOST=<HOST IP OF DB>
DB_NAME=<NAME OF DB>
DB_PORT=<PORT ON WHICH DB RUNS>
DB_TABLE_WEATHER=<TABLE NAME FOR WEATHER DATA>
DB_TABLE_RKI=<TABLE NAME FOR RKI DATA>
SAMPLING_TIME=<FETCH EVERY x SECONDS>
LOW_TEMP_THRESHOLD=<LOW TEMP AT WHICH TO NOTIFY>
HIGH_TEMP_THRESHOLD=<HIGH TEMP AT WHICH TO NOTIFY>
API_KEY=<TOKEN FOR openweathermap API>
MAIL_USER=<EMAIL OF SENDER>
MAIL_PASSWORD=<PASSWORD OF SENDER>
MAIL_HOST=<MAIL HOST SERVER>
MAIL_PORT=<MAIL HOST PORT>
MAIL_RECIPIENT=<EMAIL OF RECEIVER>
```

## Usage

This tool consists of 3 components (each in its own subdirectory):

1. data-fetcher
2. db-age-notifier
3. temp-notifier

The core part is the data-fetcher, which makes the GET requests to the APIs and stores data into the database. Parts 2 and 3 are additional support tools that monitor the age of the database (i.e. when was it last updated) and the current temperature (i.e. has it reached high or low threshold), respectively. Each of them will send an email notification (with a nice gif) when the database is too old or when the temperature has reached a lower or upper threshold.

You can run the tools manually by copying the .env file to each of the subdirectories and invoking:

```
python3 <subdirectory>/src/app.py
```

A more convenient way is too run the tools as Docker containers. Simply run Docker Compose via:

```
docker-compose up --build -d
```

The base images selected in the Dockerfiles are specifically tailored to a RaspberryPi ARMv7 architecture.

**INFO**
When running the containers on a raspberry pi using docker-compose you have to make sure that name resolution (DNS) is properly configured for the containers. On a pi one has to manually create the file `/etc/docker/daemon.json` and specify the IP of the host that runs the containers as follows (the other two are just standard google IPs as fallback):

```
{
    "dns": ["<HOST IP>", "8.8.8.8", "8.8.4.4"]
}
```
