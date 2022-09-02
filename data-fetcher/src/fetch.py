import datetime
import json
import requests

class Fetcher:
    """ Class representing a data fetcher by making HTTP requests to various APIs """

    def __init__(self, runNo: int, config: dict):
        self.runNo = runNo
        self.config = config

    def get_time_now(self):
        timestamp = datetime.datetime.utcnow().isoformat()

        return timestamp

    def check_status_api(self):
        """ Get response from status api for date check"""

        url = "https://services7.arcgis.com/mOBPykOjAyBO2ZKk/arcgis/rest/services/rki_service_status_v/FeatureServer/0/query?"
        parameter = {
            'referer': 'https://www.mywebapp.com',
            'user-agent': 'python-requests/2.9.1',
            'where': '1=1',
            'outFields': '*',
            'returnGeometry': False,
            'f': 'json',
            'cacheHint': True
        }
        response = requests.get(url=url, params=parameter)  # Anfrage absetzen
        responsejson = json.loads(response.text)  # Das Ergebnis JSON als Python Dictionary laden


        date_unix_time = responsejson['features'][-1]['attributes']['Datum']
        date = datetime.datetime.fromtimestamp(int(date_unix_time / 1000)).strftime('%Y-%m-%d')

        return date

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
        api_key = self.config['openweatherapi']['api_key']
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

    def prepare_datapoints_weather(self):
        """ Create Influxdb datapoints (using lineprotocol as of Influxdb >1.1) """

        wetter_daten = self.get_weather()

        datapoints = [
            {
                "measurement": self.config['influxdb']['table_weather'],
                "tags": {"runNum": self.runNo},
                "time": self.get_time_now(),
                "fields": {
                    "wetter": wetter_daten['weather'][0]['description'],
                    "temperatur": wetter_daten['main']['temp'] - 273.15,
                    "luftdruck": wetter_daten['main']['pressure'],
                    "luftfeuchte": wetter_daten['main']['humidity'],
                    "sichtweite": wetter_daten['visibility'],
                    "wind": wetter_daten['wind']['speed']
                }
            }
        ]

        return datapoints

    def prepare_datapoints_rki(self):
        """ Create Influxdb datapoints (using lineprotocol as of Influxdb >1.1) """

        rki_daten = self.get_inzidenz()

        datapoints = [
            {
                "measurement": self.config['influxdb']['table_rki'],
                "tags": {"runNum": self.runNo},
                "time": self.get_time_now(),
                "fields": {
                    'AdmUnitId': rki_daten['AdmUnitId'],
                    'BundeslandId': rki_daten['BundeslandId'],
                    'AnzFall': rki_daten['AnzFall'],
                    'AnzTodesfallNeu': rki_daten['AnzTodesfallNeu'],
                    'AnzFall7T': rki_daten['AnzFall7T'],
                    'AnzGenesen': rki_daten['AnzGenesen'],
                    'AnzGenesenNeu': rki_daten['AnzGenesenNeu'],
                    'AnzAktiv': rki_daten['AnzAktiv'],
                    'AnzAktivNeu': rki_daten['AnzAktivNeu'],
                    'ObjectId': rki_daten['ObjectId'],
                    "Inz7T": float(rki_daten['Inz7T']),
                    "AnzFallNeu": rki_daten['AnzFallNeu'],
                    "AnzTodesfall": rki_daten['AnzTodesfall']
                }
            }
        ]

        return datapoints
