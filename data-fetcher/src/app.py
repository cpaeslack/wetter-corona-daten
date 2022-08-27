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
    # date_now = datetime.datetime.now().strftime("%Y-%d-%m")
    # session = "Session_{}".format(date_now)
    session = config['influxdb']['table']
    runNo = 1
    be_verbose = False

    database = Database(config['influxdb'])
    fetcher = Fetcher(runNo, session, config['openweatherapi'])

    data = fetcher.prepare_datapoints()
    database.save_to_database(data, be_verbose)

if __name__ == '__main__':
    main()