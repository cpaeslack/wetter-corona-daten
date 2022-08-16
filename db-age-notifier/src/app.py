import datetime
from dotenv import load_dotenv
from influxdb import InfluxDBClient
import logging
import os
from threading import Thread
import time

def main():
    """Main loop of the program, calls the subprocesses after 5 min if they are not running"""

    # Set format of log messages
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt='[%Y-%m-%d %H:%M:%S]',
        level=logging.INFO)

    # Read credentials/config from .env file
    load_dotenv()
    config = {
        "influxdb": {
            "username": os.environ.get("USERNAME"),
            "password": os.environ.get("PASSWORD"),
            "host": os.environ.get("HOST"),
            "dbname": os.environ.get("DBNAME"),
            "port": os.environ.get("PORT")
        },
        "slack": {
            "token": os.environ["SLACK_API_TOKEN"],
            "channel": os.environ.get("SLACK_CHANNEL")
        }
    }

    # Start processes to get latest row from database and check data age
    while True:
        try:
            # Initialize the thread
            thread = Thread(target=message_poster, args=(config,))
            logging.info("Child thread started: message_poster")
            thread.start()
            while thread.is_alive():
                thread.join(300)
                logging.info("Child thread stopped: message_poster")
        except RuntimeError as error:
            logging.error(error)
        except (KeyboardInterrupt, SystemExit):
            print('Application terminated by keyboard interrupt (ctrl-c).')
            sys.exit()
        time.sleep(300)


class Database:
    """Class representing the influxdb database"""

    def __init__(self, credentials: dict):
        """Init for the Database, establishes connection to postgres"""

        self.host = credentials['host']
        self.user = credentials['username']
        self.password = credentials['password']
        self.database = credentials['dbname']
        self.port = credentials['port']
        self.client = InfluxDBClient(self.host, self.port, self.user, self.password, self.database)

    def read_latest_datapoint(self):
        latest = self.client.query('SELECT * FROM "Session_2022-17-05" ORDER BY DESC LIMIT 1;')

        return latest

def get_timestamp(database):
    """ get timestamp of latest entry in database """

    latest_entry = database.read_latest_datapoint()
    result_to_dict = list(latest_entry)[0][0]
    timestamp = result_to_dict['time']

    return timestamp

def message_poster(config: dict):

    # Establish connection to influxdb
    database = Database(config['influxdb'])

    # get current time
    date_now = datetime.datetime.now()
    logging.info(f"Current time: {date_now}")

    # get database age
    timestamp = get_timestamp(database)
    timestamp_conv = datetime.datetime.strptime(timestamp[:-1], '%Y-%m-%dT%H:%M:%S.%f') + datetime.timedelta(hours=-5, minutes=00)
    logging.info(f"Latest database timestamp: {timestamp_conv}")

    delta = date_now - timestamp_conv
    age_in_hours = round(delta.days * 24 + delta.seconds /3600)
    logging.info(f"Data base age: {age_in_hours}")

    if age_in_hours > 1:
        message = f':warning: Database older than 1 hour! ({age_in_hours} hours) :warning:'
        channel = config["slack"]["channel"]
        logging.info(message)
        try:
            post_slack_message(token, message, channel)
            logging.info(f"Sent message to Slack channel '{channel}'")
        except RuntimeError:
            logging.error("Error sending slack message!")

if __name__ == '__main__':
    main()
