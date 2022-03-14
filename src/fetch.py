import datetime
import json
import requests

class Fetcher:
    """ Class representing a data fetcher by making HTTP requests to various APIs """

    def __init__(self, runNo: int, session: str, config: dict):
        self.runNo = runNo
        self.session = session
        self.config = config

    def get_time_now(self):
        timestamp = datetime.datetime.utcnow().isoformat()

        return timestamp

    def get_inzidenz(self):
        """ Function to retrieve the 7-day incidence value from the RKI API """

        url = "https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/rki_key_data_v/FeatureServer/0/query?"
        lk_id = 5911  # ID für den Kreis Bochum gemäß AdmUnit Tabelle

        parameter = {
            'referer': 'https://www.mywebapp.com',
            'user-agent': 'python-requests/2.9.1',
            'where': f'AdmUnitId = {lk_id}',  # Welche Landkreise sollen zurückgegeben werden
            'outFields': '*',  # Rückgabe aller Felder
            'returnGeometry': False,  # Keine Geometrien
            'f': 'json',  # Rückgabeformat, hier JSON
            'cacheHint': True  # Zugriff über CDN anfragen
        }

        response = requests.get(url=url, params=parameter)
        result = json.loads(response.text)

        return result['features'][0]['attributes']

    def get_weather(self):
        """ Function to retrieve weather data from the openweathermap API """

        url = "http://api.openweathermap.org/data/2.5/weather?"
        api_key = self.config['api_key']
        latitude = "51.474810"
        longitude = "7.120350"

        parameter = {
            'lat': f'{latitude}',
            'lon': f'{longitude}',
            'appid': f'{api_key}'
        }

        response = requests.get(url=url, params=parameter)
        result = json.loads(response.text)

        return result

    def prepare_datapoints(self):
        """ Create Influxdb datapoints (using lineprotocol as of Influxdb >1.1) """

        rki_daten = self.get_inzidenz()
        wetter_daten = self.get_weather()

        datapoints = [
            {
                "measurement": self.session,
                "tags": {"runNum": self.runNo},
                "time": self.get_time_now(),
                "fields": {
                    "Inz7T": rki_daten['Inz7T'],
                    "AnzFallNeu": rki_daten['AnzFallNeu'],
                    "AnzTodesfall": rki_daten['AnzTodesfall'],
                    "wetter": wetter_daten['weather'][0]['description'],
                    "temperatur": wetter_daten['main']['temp'] - 273.15,
                    "luftdruck": wetter_daten['main']['pressure'],
                    "luftfeuchte": wetter_daten['main']['humidity'],
                    "sichtweite": wetter_daten['visibility'],
                    "wind": wetter_daten['wind']['speed'],
                }
            }
        ]

        return datapoints
