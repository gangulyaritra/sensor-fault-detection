import sys
import pandas as pd
import numpy as np
from imblearn.combine import SMOTETomek
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import RobustScaler
from sklearn.pipeline import Pipeline

from sensor.constant.training_pipeline import TARGET_COLUMN
from sensor.entity.artifact_entity import (
    DataTransformationArtifact,
    DataValidationArtifact,
)
from sensor.entity.config_entity import DataTransformationConfig
from sensor.ml.model.estimator import TargetValueMapping
from sensor.utils import save_numpy_array_data, save_object
from sensor.exception import SensorException
from sensor.logger import logging


class DataTransformation:
    """
    The Transform component performs feature engineering on the dataset
    before passing it to the model as a part of the training process.
    """

    def __init__(
        self,
        data_validation_artifact: DataValidationArtifact,
        data_transformation_config: DataTransformationConfig,
    ):
        try:
            self.data_validation_artifact = data_validation_artifact
            self.data_transformation_config = data_transformation_config
        except Exception as e:
            raise SensorException(e, sys) from e

    @staticmethod
    def read_data(file_path) -> pd.DataFrame:
        try:
            return pd.read_csv(file_path)
        except Exception as e:
            raise SensorException(e, sys) from e

    @classmethod
    def get_data_transformer_object(cls) -> Pipeline:
        """
        Function to perform missing value imputation and feature scaling.
        :return: Pipeline object to transform dataset.
        """
        try:
            return Pipeline(
                steps=[
                    ("Imputer", SimpleImputer(strategy="constant", fill_value=0)),
                    ("RobustScaler", RobustScaler()),
                ]
            )
        except Exception as e:
            raise SensorException(e, sys) from e

    def initiate_data_transformation(self) -> DataTransformationArtifact:
        try:
            logging.info(">> Data Transformation Component Started.")
            preprocessor = self.get_data_transformer_object()

            train_df = DataTransformation.read_data(
                file_path=self.data_validation_artifact.valid_train_file_path
            )
            test_df = DataTransformation.read_data(
                file_path=self.data_validation_artifact.valid_test_file_path
            )

            # Train Dataframe.
            input_feature_train_df = train_df.drop(columns=[TARGET_COLUMN], axis=1)
            target_feature_train_df = train_df[TARGET_COLUMN]
            target_feature_train_df = target_feature_train_df.replace(
                TargetValueMapping().to_dict()
            )

            # Test Dataframe.
            input_feature_test_df = test_df.drop(columns=[TARGET_COLUMN], axis=1)
            target_feature_test_df = test_df[TARGET_COLUMN]
            target_feature_test_df = target_feature_test_df.replace(
                TargetValueMapping().to_dict()
            )

            logging.info("Applying the Pipeline object to transform the dataset.....")
            preprocessor_object = preprocessor.fit(input_feature_train_df)
            transformed_input_train_feature = preprocessor_object.transform(
                input_feature_train_df
            )
            transformed_input_test_feature = preprocessor_object.transform(
                input_feature_test_df
            )

            smt = SMOTETomek(sampling_strategy="minority")

            logging.info("Applying SMOTETomek to handle the imbalanced dataset.....")
            input_feature_train_final, target_feature_train_final = smt.fit_resample(
                transformed_input_train_feature, target_feature_train_df
            )
            input_feature_test_final, target_feature_test_final = smt.fit_resample(
                transformed_input_test_feature, target_feature_test_df
            )

            train_arr = np.c_[
                input_feature_train_final, np.array(target_feature_train_final)
            ]
            test_arr = np.c_[
                input_feature_test_final, np.array(target_feature_test_final)
            ]

            save_object(
                self.data_transformation_config.transformed_object_file_path,
                preprocessor_object,
            )
            save_numpy_array_data(
                self.data_transformation_config.transformed_train_file_path,
                array=train_arr,
            )
            save_numpy_array_data(
                self.data_transformation_config.transformed_test_file_path,
                array=test_arr,
            )

            data_transformation_artifact = DataTransformationArtifact(
                transformed_object_file_path=self.data_transformation_config.transformed_object_file_path,
                transformed_train_file_path=self.data_transformation_config.transformed_train_file_path,
                transformed_test_file_path=self.data_transformation_config.transformed_test_file_path,
            )
            logging.info(
                f"Data Transformation Artifact: [{data_transformation_artifact}]."
            )
            logging.info(">> Data Transformation Component Ended.")

        except Exception as e:
            raise SensorException(e, sys) from e
