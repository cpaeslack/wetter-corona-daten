import datetime
from dotenv import load_dotenv
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from influxdb import InfluxDBClient
import logging
import os
import smtplib
from threading import Thread
import time

def main():
    """Main loop of the program, calls the subprocesses after 30 min if they are not running"""

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
        self.client = InfluxDBClient(self.host, self.port, self.user, self.password, self.database)

    def read_latest_datapoint(self):
        latest = self.client.query('SELECT * FROM "Session_2022-17-05" ORDER BY DESC LIMIT 1;')

        return latest

def get_temperature(database):
    """ get timestamp of latest entry in database """

    latest_entry = database.read_latest_datapoint()
    result_to_dict = list(latest_entry)[0][0]
    temperature = result_to_dict['temperatur']

    return temperature

def send_mail(config, temp):
    """ sends and e-mail with warning about database age """

    mail_user = config["mail_user"]
    mail_password = config["mail_password"]
    recipient = config["mail_recipient"]
    subject = "INFO: High Temperature Notification"
    body = f"The outside temperature has reached {temp}°C, please close the windows!"
    msg = MIMEMultipart()
    msg['Subject'] = subject
    msg['From'] = mail_user
    msg['To'] = recipient
    part = MIMEText(body, 'plain')
    msg.attach(part)
    logging.info(msg)

    try:
        server = smtplib.SMTP(config["mail_host"], config["mail_port"])
        server.set_debuglevel(1)
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

    # get temperature
    temperature = get_temperature(database)
    logging.info(f"Latest temperature measurement: {round(temperature,2)}")

    # send mail if temperature has reached 24°C
    if temperature > 24:
        send_mail(config["mail"], round(temperature,2))

if __name__ == '__main__':
    main()
