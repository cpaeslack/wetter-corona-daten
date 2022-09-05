import datetime
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from email.mime.text import MIMEText
from influxdb import InfluxDBClient
import logging
import os
from pathlib import Path
import smtplib
from threading import Thread
import time


def main():
    """Main loop of the program, calls the subprocesses after 10 min if they are not running"""

    # Set format of log messages
    logging.basicConfig(
        format='%(asctime)s %(levelname)s %(message)s',
        datefmt='[%Y-%m-%d %H:%M:%S]',
        level=logging.INFO)

    # Read credentials/config from .env file
    load_dotenv()
    config = {
        "influxdb": {
            "username": os.environ["DB_USERNAME"],
            "password": os.environ["DB_PASSWORD"],
            "host": os.environ["DB_HOST"],
            "dbname": os.environ["DB_NAME"],
            "port": os.environ["DB_PORT"],
            "table": os.environ["DB_TABLE_WEATHER"]
        },
        "mail": {
            "mail_user": os.environ["MAIL_USER"],
            "mail_password": os.environ["MAIL_PASSWORD"],
            "mail_host": os.environ["MAIL_HOST"],
            "mail_port": os.environ["MAIL_PORT"],
            "mail_recipient": os.environ["MAIL_RECIPIENT"]
        },
        "thresholds": {
            "low_temp_threshold": os.environ["LOW_TEMP_THRESHOLD"],
            "high_temp_threshold": os.environ["HIGH_TEMP_THRESHOLD"]
        }
    }

    # Start processes to get latest row from database and check data age
    sampling_time = int(os.environ["SAMPLING_TIME"])
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
        time.sleep(sampling_time)


class Database:
    """Class representing the influxdb database"""

    def __init__(self, credentials: dict):
        """Init for the Database, establishes connection to postgres"""

        self.host = credentials['host']
        self.user = credentials['username']
        self.password = credentials['password']
        self.database = credentials['dbname']
        self.port = credentials['port']
        self.table = credentials['table']
        self.client = InfluxDBClient(
            self.host, self.port, self.user, self.password, self.database)

    def read_latest_datapoint(self):
        latest = self.client.query(
            f'SELECT * FROM "{self.table}" ORDER BY DESC LIMIT 1;')

        return latest


def get_temperature(database):
    """ get timestamp of latest entry in database """

    latest_entry = database.read_latest_datapoint()
    result_to_dict = list(latest_entry)[0][0]
    temperature = result_to_dict['temperatur']

    return temperature


def send_mail(config, temp, temp_case):
    """ sends and e-mail with warning about database age """

    mail_user = config["mail_user"]
    mail_password = config["mail_password"]
    recipient = config["mail_recipient"]
    if temp_case == "high_temp":
        subject = "INFO: High Temperature Notification"
        body = f"""The outside temperature has reached {temp}°C!
            \n
        """
    elif temp_case == "low_temp":
        subject = "INFO: Low Temperature Notification"
        body = f"""The outside temperature has dropped below {temp}°C!
            \n
        """
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = mail_user
    msg['To'] = recipient
    part = MIMEText(body, 'plain')
    msg.attach(part)

    # read gif file and attach to mail
    filename = f"gif_{temp_case}.gif"
    part2 = MIMEBase('application', "octet-stream")
    with open(filename, 'rb') as file:
        part2.set_payload(file.read())
    encoders.encode_base64(part2)
    part2.add_header('Content-Disposition',
                     'attachment; filename={}'.format(Path(filename).name))
    msg.attach(part2)

    try:
        # server = smtplib.SMTP(config["mail_host"], config["mail_port"])
        # # server.set_debuglevel(1)
        # server.starttls()
        # server.login(mail_user, mail_password)
        # server.sendmail(mail_user, recipient, msg.as_string())
        # server.close()
        logging.info(f"Successfully sent email to {recipient}!")
    except:
        logging.error("ERROR: unable to send email")


def message_poster(config: dict):
    """ Gets the hours since last db update and posts
        and sends an e-mail when database older than 1 hour.
    """

    # Establish connection to influxdb
    database = Database(config['influxdb'])

    # get current time
    date_now = datetime.datetime.now()

    # get temperature
    temperature = get_temperature(database)
    logging.info(f"Latest temperature measurement: {round(temperature,2)}")

    # get thresholds
    low_temp_threshold = int(config['thresholds']['low_temp_threshold'])
    high_temp_threshold = int(config['thresholds']['high_temp_threshold'])

    logging.info(f"low_temp_threshold= {low_temp_threshold}")
    logging.info(f"high_temp_threshold= {high_temp_threshold}")

    # send mail only once when temperature has passes threshold (hot or cold)
    file_exists_high = Path("high_temp").is_file()
    file_exist_low = Path("low_temp").is_file()

    if temperature >= high_temp_threshold and file_exists_high is False:
        send_mail(config["mail"], round(temperature, 2), "high_temp")
        Path("high_temp").touch()
    if temperature < high_temp_threshold and file_exists_high is True:
        os.remove("high_temp")
    if temperature < low_temp_threshold and file_exist_low is False:
        send_mail(config["mail"], round(temperature, 2), "low_temp")
        Path("low_temp").touch()
    if temperature >= low_temp_threshold and file_exist_low is True:
        os.remove("low_temp")


if __name__ == '__main__':
    main()
