import logging

from influxdb import InfluxDBClient

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

    def save_to_database(self, data: list, be_verbose: bool):
        """ Store the recorded data in the database """

        try:
            bResult = self.client.write_points(data)
            if be_verbose:
                print("Write points {0} Bresult:{1}".format(data,bResult))
            logging.info(f"Saved data in database '{self.database}' successfully!")
        except (InfluxDBClientError, InfluxDBServerError) as err:
            raise RuntimeError(err)
