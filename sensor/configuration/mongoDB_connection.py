import os
import sys
import certifi
import pymongo
from sensor.constant.constant import DATABASE_NAME, MONGO_DB_URL
from sensor.exception import SensorException

ca = certifi.where()


class MongoDBClient:
    client = None

    def __init__(self, database_name=DATABASE_NAME) -> None:
        try:
            if MongoDBClient.client is None:
                mongo_db_url = os.getenv(MONGO_DB_URL)
                if "localhost" in mongo_db_url:
                    MongoDBClient.client = pymongo.MongoClient(mongo_db_url)
                else:
                    MongoDBClient.client = pymongo.MongoClient(
                        mongo_db_url, tlsCAFile=ca
                    )
            self.client = MongoDBClient.client
            self.database = self.client[database_name]
            self.database_name = database_name

        except Exception as e:
            raise SensorException(e, sys) from e
