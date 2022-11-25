import sys
import pandas as pd

from sensor.constant.training_pipeline import TARGET_COLUMN
from sensor.entity.artifact_entity import (
    DataValidationArtifact,
    ModelTrainerArtifact,
    ModelEvaluationArtifact,
)
from sensor.entity.config_entity import ModelEvaluationConfig
from sensor.exception import SensorException
from sensor.logger import logging
from sensor.ml.metric.classification_metric import get_classification_score
from sensor.ml.model.estimator import TargetValueMapping, ModelResolver
from sensor.utils import load_object, write_yaml_file

"""
The Evaluator component performs a deep analysis of the training results for our models 
to help us understand how our model performs on subsets of the data. The Evaluator also 
validates our exported models, ensuring to be "good enough" to get pushed to production.

When validation is enabled, the Evaluator compares new models against a baseline model to 
determine if they're "good enough" relative to the baseline. It does so by evaluating both 
models on an inference dataset and computing their performance on metrics (e.g., AUC, loss). 
If the new model's metrics outperform the baseline model, the model is "blessed" indicating 
the Pusher component to push the model into production.
"""


class ModelEvaluation:
    def __init__(
        self,
        model_evaluation_config: ModelEvaluationConfig,
        data_validation_artifact: DataValidationArtifact,
        model_trainer_artifact: ModelTrainerArtifact,
    ):
        try:
            self.model_evaluation_config = model_evaluation_config
            self.data_validation_artifact = data_validation_artifact
            self.model_trainer_artifact = model_trainer_artifact
        except Exception as e:
            raise SensorException(e, sys) from e

    def initiate_model_evaluation(self) -> ModelEvaluationArtifact:
        try:
            logging.info(">> Model Evaluation Component Started.")

            train_df = pd.read_csv(self.data_validation_artifact.valid_train_file_path)
            test_df = pd.read_csv(self.data_validation_artifact.valid_test_file_path)

            df = pd.concat([train_df, test_df])
            y_true = df[TARGET_COLUMN]
            y_true.replace(TargetValueMapping().to_dict(), inplace=True)
            df.drop(TARGET_COLUMN, axis=1, inplace=True)

            train_model_file_path = self.model_trainer_artifact.trained_model_file_path
            model_resolver = ModelResolver()
            is_model_accepted = True

            if not model_resolver.is_model_exists():
                model_evaluation_artifact = ModelEvaluationArtifact(
                    is_model_accepted=is_model_accepted,
                    improved_accuracy=None,
                    best_model_path=None,
                    trained_model_path=train_model_file_path,
                    train_model_metric_artifact=self.model_trainer_artifact.test_metric_artifact,
                    best_model_metric_artifact=None,
                )
                logging.info(
                    f"Model Evaluation Artifact: [{model_evaluation_artifact}]."
                )
                return model_evaluation_artifact

            latest_model_path = model_resolver.get_best_model_path()
            latest_model = load_object(file_path=latest_model_path)
            train_model = load_object(file_path=train_model_file_path)

            y_trained_pred = train_model.predict(df)
            y_latest_pred = latest_model.predict(df)

            trained_metric = get_classification_score(y_true, y_trained_pred)
            latest_metric = get_classification_score(y_true, y_latest_pred)

            improved_accuracy = trained_metric.f1_score - latest_metric.f1_score
            is_model_accepted = (
                self.model_evaluation_config.change_threshold < improved_accuracy
            )

            model_evaluation_artifact = ModelEvaluationArtifact(
                is_model_accepted=is_model_accepted,
                improved_accuracy=improved_accuracy,
                best_model_path=latest_model_path,
                trained_model_path=train_model_file_path,
                train_model_metric_artifact=trained_metric,
                best_model_metric_artifact=latest_metric,
            )

            model_evaluation_report = model_evaluation_artifact.__dict__

            # Save the Report.
            write_yaml_file(
                self.model_evaluation_config.report_file_path, model_evaluation_report
            )

            logging.info(f"Model Evaluation Artifact: [{model_evaluation_artifact}].")
            logging.info(">> Model Evaluation Component Ended.")
            return model_evaluation_artifact

        except Exception as e:
            raise SensorException(e, sys) from e
