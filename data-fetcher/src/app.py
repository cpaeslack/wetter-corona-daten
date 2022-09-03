import datetime
import logging
from threading import Thread
import time

from config import get_config
from db import Database
from fetch import Fetcher

def main():
    """Main loop of the program, calls the subprocesses after 10 seconds if they are not running"""

    # Set format of log messages
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt='[%Y-%m-%d %H:%M:%S]',
        level=logging.INFO)

    # Initialize the monitoring process
    process = None

    # Read credentials/config from json file
    config = get_config()

    # How frequently we will write sensor data to the database (in seconds).
    sampling_period = config['general']['sampling_time']
    logging.info(f'sampling_period: {sampling_period} sec')

    # Start processes for data retrieval from apis and writing to database
    while True:
        try:
            fetcher_thread = Thread(target=fetch_and_store_data, args=(config,))
            logging.info("Child thread started: fetch_and_store_data")
            fetcher_thread.start()
            while fetcher_thread.is_alive():
                fetcher_thread.join(sampling_period)
                logging.info("Child thread stopped: fetch_and_store_data")
        except RuntimeError as error:
            logging.error(error)
        except (KeyboardInterrupt, SystemExit):
            print('Application terminated by keyboard interrupt (ctrl-c).')
            sys.exit()
        time.sleep(sampling_period)

def fetch_and_store_data(config: dict):
    """ read out system data and store in database """

    logging.info('Starting retrieval of data.')
    date_today = datetime.datetime.now().strftime("%Y-%d-%m")
    runNo = 1
    be_verbose = False

    database = Database(config['influxdb'])
    fetcher = Fetcher(runNo, config)

    logging.info("Fetching weather data from openweathermap API")
    data_weather = fetcher.prepare_datapoints_weather()
    database.save_to_database(data_weather, be_verbose)

    date_rki = fetcher.check_status_api()
    if date_today != date_rki:
        last_object_id_in_db = list(database.get_last_object_id())[0][0]['ObjectId']
        data_rki = fetcher.prepare_datapoints_rki()
        rki_object_id = data_rki[0]['fields']['ObjectId']
        if rki_object_id != last_object_id_in_db:
            logging.info(f"object_id: {rki_object_id} not found in database")
            logging.info("Fetching Corona data from RKI API")
            database.save_to_database(data_rki, be_verbose)
        else:
            logging.info("Corona data is up to date!")

if __name__ == '__main__':
    main()