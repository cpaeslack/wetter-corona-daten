# wetter-corona-daten
***

### Description
This Python program repeatedly gets current weather and corona data from the openweatherapp and RKI APIs, respectively.
The data is then stored in a user-defined InfluxDB database and can be used to build e.g. a Grafana dashboard from it.

### Setup and usage
The easiest way to run this app is by creating a virtual environment in Python.
All dependencies are listed in `requirements.txt`. Further, make a copy of the file `config.json.template`
and name it `config.json`. It is passed when running the script. Specify the required
values for the InfluxDB name, host, user, password etc. in this file.
Finally, run the program then via `python3 src/app.py`.

Another way to run the code (specifically tailored to a RaspberryPi 4 ARMv7 architecture)
is by using the provided docker setup. Create a `.env` in the parent directory
and add the line `VERSION=XYZ` (XYZ mean type 1.0 or anything else here). Simply run the bash script `run-container.sh`
and after a successful build get the output by typing `docker logs -f wetter-corona-daten`.