import os
import sys
import pandas as pd
from scipy.stats import ks_2samp

from sensor.constant.training_pipeline import SCHEMA_FILE_PATH
from sensor.entity.artifact_entity import DataIngestionArtifact, DataValidationArtifact
from sensor.entity.config_entity import DataValidationConfig
from sensor.utils import read_yaml_file, write_yaml_file
from sensor.exception import SensorException
from sensor.logger import logging


class DataValidation:
    def __init__(
        self,
        data_ingestion_artifact: DataIngestionArtifact,
        data_validation_config: DataValidationConfig,
    ):
        try:
            self.data_ingestion_artifact = data_ingestion_artifact
            self.data_validation_config = data_validation_config
            self._schema_config = read_yaml_file(file_path=SCHEMA_FILE_PATH)
        except Exception as e:
            raise SensorException(e, sys) from e

    def validate_number_of_columns(self, dataframe: pd.DataFrame) -> bool:
        """
        :param dataframe:
        :return: Returns True if required columns are present.
        """
        try:
            return len(dataframe.columns) == len(self._schema_config["columns"])
        except Exception as e:
            raise SensorException(e, sys) from e

    def is_numerical_column_exist(self, dataframe: pd.DataFrame) -> bool:
        """
        :param dataframe:
        :return: Returns True if all numerical columns are present, else False.
        """
        try:
            dataframe_columns = dataframe.columns
            numerical_column_present = True
            missing_numerical_columns = []
            for num_column in self._schema_config["numerical_columns"]:
                if num_column not in dataframe_columns:
                    numerical_column_present = False
                    missing_numerical_columns.append(num_column)

            logging.info(f"Missing Numerical Columns: [{missing_numerical_columns}]")
            return numerical_column_present

        except Exception as e:
            raise SensorException(e, sys) from e

    @staticmethod
    def read_data(file_path) -> pd.DataFrame:
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise SensorException(e, sys) from e

    def detect_dataset_drift(self, base_df, current_df, threshold=0.05) -> bool:
        try:
            status = True
            report = {}
            for column in base_df.columns:
                d1 = base_df[column]
                d2 = current_df[column]
                is_same_dist = ks_2samp(d1, d2)
                if threshold <= is_same_dist.pvalue:
                    is_found = False
                else:
                    is_found = True
                    status = False
                report[column] = {
                    "p_value": float(is_same_dist.pvalue),
                    "drift_status": is_found,
                }

            drift_report_file_path = self.data_validation_config.drift_report_file_path

            # Create Directory.
            dir_path = os.path.dirname(drift_report_file_path)
            os.makedirs(dir_path, exist_ok=True)
            write_yaml_file(
                file_path=drift_report_file_path,
                content=report,
            )
            return status

        except Exception as e:
            raise SensorException(e, sys) from e

    def initiate_data_validation(self) -> DataValidationArtifact:
        try:
            logging.info(">> Data Validation Component Started.")
            error_message = ""

            train_df, test_df = (
                DataValidation.read_data(
                    file_path=self.data_ingestion_artifact.trained_file_path
                ),
                DataValidation.read_data(
                    file_path=self.data_ingestion_artifact.test_file_path
                ),
            )

            status = self.validate_number_of_columns(dataframe=train_df)

            if not status:
                error_message = (
                    f"{error_message} Columns are missing in the Train Dataframe.\n"
                )

            status = self.validate_number_of_columns(dataframe=test_df)

            if not status:
                error_message = (
                    f"{error_message} Columns are missing in the Test Dataframe.\n"
                )

            status = self.is_numerical_column_exist(dataframe=train_df)

            if not status:
                error_message = (
                    f"{error_message} Missing numerical columns in Train Dataframe.\n"
                )

            status = self.is_numerical_column_exist(dataframe=test_df)

            if not status:
                error_message = (
                    f"{error_message} Missing numerical columns in Test Dataframe.\n"
                )

            if error_message != "":
                raise Exception(error_message)

            # Checking Data Drift.
            status = self.detect_dataset_drift(base_df=train_df, current_df=test_df)

            data_validation_artifact = DataValidationArtifact(
                validation_status=status,
                valid_train_file_path=self.data_ingestion_artifact.trained_file_path,
                valid_test_file_path=self.data_ingestion_artifact.test_file_path,
                invalid_train_file_path=None,
                invalid_test_file_path=None,
                drift_report_file_path=self.data_validation_config.drift_report_file_path,
            )
            logging.info(f"Data Validation Artifact: [{data_validation_artifact}].")
            logging.info(">> Data Validation Component Ended.")
            return data_validation_artifact

        except Exception as e:
            raise SensorException(e, sys) from e
