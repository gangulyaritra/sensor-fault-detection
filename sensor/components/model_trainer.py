import os
import sys
from xgboost import XGBClassifier
from sensor.entity.artifact_entity import (
    DataTransformationArtifact,
    ModelTrainerArtifact,
)
from sensor.entity.config_entity import ModelTrainerConfig
from sensor.ml.metric.classification_metric import get_classification_score
from sensor.ml.model.estimator import SensorModel
from sensor.utils import load_numpy_array_data, load_object, save_object
from sensor.exception import SensorException
from sensor.logger import logging


class ModelTrainer:
    """
    The Trainer component trains a Machine Learning model.
    The Tuner component tunes the hyperparameters for the model.
    """

    def __init__(
        self,
        model_trainer_config: ModelTrainerConfig,
        data_transformation_artifact: DataTransformationArtifact,
    ):
        try:
            self.data_transformation_artifact = data_transformation_artifact
            self.model_trainer_config = model_trainer_config
        except Exception as e:
            raise SensorException(e, sys) from e

    def perform_hyperparamter_tuning(self):
        pass

    def train_model(self, X_train, y_train):
        try:
            xgb_clf = XGBClassifier()
            xgb_clf.fit(X_train, y_train)
            return xgb_clf
        except Exception as e:
            raise e

    def initiate_model_trainer(self) -> ModelTrainerArtifact:
        try:
            logging.info(">> Model Trainer Component Started.")
            train_arr = load_numpy_array_data(
                file_path=self.data_transformation_artifact.transformed_train_file_path
            )
            test_arr = load_numpy_array_data(
                file_path=self.data_transformation_artifact.transformed_test_file_path
            )
            X_train, y_train, X_test, y_test = (
                train_arr[:, :-1],
                train_arr[:, -1],
                test_arr[:, :-1],
                test_arr[:, -1],
            )

            model = self.train_model(X_train, y_train)
            y_train_pred = model.predict(X_train)

            classification_train_metric = get_classification_score(
                y_true=y_train, y_pred=y_train_pred
            )

            if (
                classification_train_metric.f1_score
                <= self.model_trainer_config.expected_accuracy
            ):
                raise Exception(
                    "The trained model is unable to provide the expected accuracy."
                )

            y_test_pred = model.predict(X_test)
            classification_test_metric = get_classification_score(
                y_true=y_test, y_pred=y_test_pred
            )

            # Overfitting and Underfitting.
            diff = abs(
                classification_train_metric.f1_score
                - classification_test_metric.f1_score
            )

            if diff > self.model_trainer_config.overfitting_underfitting_threshold:
                raise Exception(
                    "The trained model is not generalized. Try more experimentation."
                )

            preprocessor = load_object(
                file_path=self.data_transformation_artifact.transformed_object_file_path
            )

            model_dir_path = os.path.dirname(
                self.model_trainer_config.trained_model_file_path
            )
            os.makedirs(model_dir_path, exist_ok=True)

            sensor_model = SensorModel(preprocessor=preprocessor, model=model)
            save_object(
                self.model_trainer_config.trained_model_file_path, obj=sensor_model
            )

            model_trainer_artifact = ModelTrainerArtifact(
                trained_model_file_path=self.model_trainer_config.trained_model_file_path,
                train_metric_artifact=classification_train_metric,
                test_metric_artifact=classification_test_metric,
            )

            logging.info(f"Model Trainer Artifact: [{model_trainer_artifact}].")
            logging.info(">> Model Trainer Component Ended.")
            return model_trainer_artifact

        except Exception as e:
            raise SensorException(e, sys) from e
