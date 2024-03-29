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
            "username": os.environ["DB_USERNAME"],
            "password": os.environ["DB_PASSWORD"],
            "host": os.environ["DB_HOST"],
            "dbname": os.environ["DB_NAME"],
            "port": os.environ["DB_PORT"],
            "table_weather": os.environ["DB_TABLE_WEATHER"],
            "table_rki": os.environ["DB_TABLE_RKI"]
        },
        "mail": {
            "mail_user": os.environ["MAIL_USER"],
            "mail_password": os.environ["MAIL_PASSWORD"],
            "mail_host": os.environ["MAIL_HOST"],
            "mail_port": os.environ["MAIL_PORT"],
            "mail_recipient": os.environ["MAIL_RECIPIENT"]
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
        time.sleep(1800)


class Database:
    """Class representing the influxdb database"""

    def __init__(self, credentials: dict):
        """Init for the Database, establishes connection to postgres"""

        self.host = credentials['host']
        self.user = credentials['username']
        self.password = credentials['password']
        self.database = credentials['dbname']
        self.port = credentials['port']
        self.table_weather = credentials['table_weather']
        self.table_rki = credentials['table_rki']
        self.client = InfluxDBClient(self.host, self.port, self.user, self.password, self.database)

    def read_latest_datapoint(self):
        latest = self.client.query(f'SELECT * FROM {self.table_weather} ORDER BY DESC LIMIT 1;')

        return latest

def get_timestamp(database):
    """ get timestamp of latest entry in database """

    latest_entry = database.read_latest_datapoint()
    result_to_dict = list(latest_entry)[0][0]
    timestamp = result_to_dict['time']

    return timestamp

def send_mail(config, age):
    """ sends and e-mail with warning about database age """

    mail_user = config["mail_user"]
    mail_password = config["mail_password"]
    recipient = config["mail_recipient"]
    subject = "WARNING: Database Age Alert"
    body = f"""Database was last updated {age} hours ago!
        \n
    """
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = mail_user
    msg['To'] = recipient
    part = MIMEText(body, 'plain')
    msg.attach(part)
    logging.info(msg)

    # read gif file and attach to mail
    filename = "giphy.gif"
    part2 = MIMEBase('application', "octet-stream")
    with open(filename, 'rb') as file:
        part2.set_payload(file.read())
    encoders.encode_base64(part2)
    part2.add_header('Content-Disposition',
                    'attachment; filename={}'.format(Path(filename).name))
    msg.attach(part2)

    try:
        server = smtplib.SMTP(config["mail_host"], config["mail_port"])
        # server.set_debuglevel(1)
        server.starttls()
        server.login(mail_user, mail_password)
        server.sendmail(mail_user, recipient, msg.as_string())
        server.close()
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
    logging.info(f"Current time: {date_now}")

    # get database age
    timestamp = get_timestamp(database)
    timestamp_conv = datetime.datetime.strptime(timestamp[:-1], '%Y-%m-%dT%H:%M:%S.%f')
    #+ datetime.timedelta(hours=2, minutes=00)
    logging.info(f"Latest database timestamp: {timestamp_conv}")

    delta = date_now - timestamp_conv
    age_in_hours = round(delta.days * 24 + delta.seconds /3600)
    logging.info(f"Data base age: {age_in_hours} hours")

    # send mail if database is too old
    if age_in_hours > 1:
        send_mail(config["mail"], age_in_hours)

if __name__ == '__main__':
    main()
