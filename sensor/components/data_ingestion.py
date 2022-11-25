import os
import sys
from pandas import DataFrame
from sklearn.model_selection import train_test_split

from sensor.constant.training_pipeline import SCHEMA_FILE_PATH
from sensor.data_access.sensor_data import SensorData
from sensor.utils import read_yaml_file
from sensor.entity.artifact_entity import DataIngestionArtifact
from sensor.entity.config_entity import DataIngestionConfig
from sensor.exception import SensorException
from sensor.logger import logging


class DataIngestion:
    """
    Data ingestion is a process of transporting data from different sources to
    a target site for immediate use, such as further processing and analysis.
    """

    def __init__(self, data_ingestion_config: DataIngestionConfig):
        try:
            self.data_ingestion_config = data_ingestion_config
            self._schema_config = read_yaml_file(SCHEMA_FILE_PATH)
        except Exception as e:
            raise SensorException(e, sys) from e

    def export_data_into_feature_store(self) -> DataFrame:
        try:
            logging.info("Exporting data from MongoDB to Feature Store.")
            sensor_data = SensorData()
            dataframe = sensor_data.export_collection_as_dataframe(
                collection_name=self.data_ingestion_config.collection_name
            )
            feature_store_file_path = self.data_ingestion_config.feature_store_file_path
            dir_path = os.path.dirname(feature_store_file_path)
            os.makedirs(dir_path, exist_ok=True)
            dataframe.to_csv(feature_store_file_path, index=False, header=True)
            return dataframe

        except Exception as e:
            raise SensorException(e, sys) from e

    def split_data_as_train_test(self, dataframe: DataFrame) -> None:
        """
        This method splits the Dataframe into train and test sets based on a split ratio.
        """
        try:
            logging.info("Splitting Dataset into Train and Test Sets......")
            train_set, test_set = train_test_split(
                dataframe, test_size=self.data_ingestion_config.train_test_split_ratio
            )
            dir_path = os.path.dirname(self.data_ingestion_config.training_file_path)
            os.makedirs(dir_path, exist_ok=True)

            logging.info("Export train and test file path.")
            train_set.to_csv(
                self.data_ingestion_config.training_file_path, index=False, header=True
            )
            test_set.to_csv(
                self.data_ingestion_config.testing_file_path, index=False, header=True
            )

        except Exception as e:
            raise SensorException(e, sys) from e

    def initiate_data_ingestion(self) -> DataIngestionArtifact:
        try:
            logging.info(">> Data Ingestion Component Started.")
            dataframe = self.export_data_into_feature_store()
            dataframe = dataframe.drop(self._schema_config["drop_columns"], axis=1)
            self.split_data_as_train_test(dataframe=dataframe)
            data_ingestion_artifact = DataIngestionArtifact(
                trained_file_path=self.data_ingestion_config.training_file_path,
                test_file_path=self.data_ingestion_config.testing_file_path,
            )
            logging.info(f"Data Ingestion Artifact: [{data_ingestion_artifact}].")
            logging.info(">> Data Ingestion Component Ended.")
            return data_ingestion_artifact

        except Exception as e:
            raise SensorException(e, sys) from e
