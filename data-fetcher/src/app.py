import logging
from multiprocessing import Process
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
            if process is None or not process.is_alive():
                process = Process(
                    target=fetch_and_store_data, args=(config,))
                process.start()
        except RuntimeError as error:
            logging.error(error)
        except KeyboardInterrupt:
            print('Application terminated by keyboard interrupt (ctrl-c).')
        time.sleep(sampling_period)

def fetch_and_store_data(config: dict):
    """ read out system data and store in database """

    logging.info('Starting retrieval of data.')
    # date_now = datetime.datetime.now().strftime("%Y-%d-%m")
    # session = "Session_{}".format(date_now)
    session = "Session_2022-03-14"
    runNo = 1
    be_verbose = False

    database = Database(config['influxdb'])
    fetcher = Fetcher(runNo, session, config['openweatherapi'])

    data = fetcher.prepare_datapoints()
    database.save_to_database(data, be_verbose)

if __name__ == '__main__':
    main()