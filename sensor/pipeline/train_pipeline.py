import sys

from sensor.components.data_ingestion import DataIngestion
from sensor.components.data_validation import DataValidation
from sensor.components.data_transformation import DataTransformation
from sensor.components.model_trainer import ModelTrainer
from sensor.components.model_evaluation import ModelEvaluation
from sensor.components.model_pusher import ModelPusher
from sensor.cloud_storage.s3_syncer import S3Sync
from sensor.constant.constant import S3_BUCKET_NAME
from sensor.constant.training_pipeline import SAVED_MODEL_DIR
from sensor.entity.artifact_entity import (
    DataIngestionArtifact,
    DataValidationArtifact,
    DataTransformationArtifact,
    ModelTrainerArtifact,
    ModelEvaluationArtifact,
)
from sensor.entity.config_entity import (
    TrainingPipelineConfig,
    DataIngestionConfig,
    DataValidationConfig,
    DataTransformationConfig,
    ModelTrainerConfig,
    ModelEvaluationConfig,
    ModelPusherConfig,
)
from sensor.exception import SensorException
from sensor.logger import logging


class TrainPipeline:
    is_pipeline_running = False

    def __init__(self):
        self.training_pipeline_config = TrainingPipelineConfig()
        self.s3_sync = S3Sync()

    def start_data_ingestion(self) -> DataIngestionArtifact:
        try:
            self.data_ingestion_config = DataIngestionConfig(
                training_pipeline_config=self.training_pipeline_config
            )
            data_ingestion = DataIngestion(
                data_ingestion_config=self.data_ingestion_config
            )
            return data_ingestion.initiate_data_ingestion()

        except Exception as e:
            raise SensorException(e, sys) from e

    def start_data_validaton(
        self, data_ingestion_artifact: DataIngestionArtifact
    ) -> DataValidationArtifact:
        try:
            data_validation_config = DataValidationConfig(
                training_pipeline_config=self.training_pipeline_config
            )
            data_validation = DataValidation(
                data_ingestion_artifact=data_ingestion_artifact,
                data_validation_config=data_validation_config,
            )
            return data_validation.initiate_data_validation()

        except Exception as e:
            raise SensorException(e, sys) from e

    def start_data_transformation(
        self, data_validation_artifact: DataValidationArtifact
    ):
        try:
            data_transformation_config = DataTransformationConfig(
                training_pipeline_config=self.training_pipeline_config
            )
            data_transformation = DataTransformation(
                data_validation_artifact=data_validation_artifact,
                data_transformation_config=data_transformation_config,
            )
            return data_transformation.initiate_data_transformation()

        except Exception as e:
            raise SensorException(e, sys) from e

    def start_model_trainer(
        self, data_transformation_artifact: DataTransformationArtifact
    ):
        try:
            model_trainer_config = ModelTrainerConfig(
                training_pipeline_config=self.training_pipeline_config
            )
            model_trainer = ModelTrainer(
                model_trainer_config, data_transformation_artifact
            )
            return model_trainer.initiate_model_trainer()

        except Exception as e:
            raise SensorException(e, sys) from e

    def start_model_evaluation(
        self,
        data_validation_artifact: DataValidationArtifact,
        model_trainer_artifact: ModelTrainerArtifact,
    ):
        try:
            model_evaluation_config = ModelEvaluationConfig(
                self.training_pipeline_config
            )
            model_evaluation = ModelEvaluation(
                model_evaluation_config,
                data_validation_artifact,
                model_trainer_artifact,
            )
            return model_evaluation.initiate_model_evaluation()

        except Exception as e:
            raise SensorException(e, sys) from e

    def start_model_pusher(self, model_evaluation_artifact: ModelEvaluationArtifact):
        try:
            model_pusher_config = ModelPusherConfig(
                training_pipeline_config=self.training_pipeline_config
            )
            model_pusher = ModelPusher(model_pusher_config, model_evaluation_artifact)
            return model_pusher.initiate_model_pusher()

        except Exception as e:
            raise SensorException(e, sys) from e

    def sync_artifact_dir_to_s3(self):
        try:
            aws_bucket_url = f"s3://{S3_BUCKET_NAME}/artifact/{self.training_pipeline_config.timestamp}"
            self.s3_sync.sync_folder_to_s3(
                folder=self.training_pipeline_config.artifact_dir,
                aws_bucket_url=aws_bucket_url,
            )

        except Exception as e:
            raise SensorException(e, sys) from e

    def sync_saved_model_dir_to_s3(self):
        try:
            aws_bucket_url = f"s3://{S3_BUCKET_NAME}/{SAVED_MODEL_DIR}"
            self.s3_sync.sync_folder_to_s3(
                folder=SAVED_MODEL_DIR, aws_bucket_url=aws_bucket_url
            )

        except Exception as e:
            raise SensorException(e, sys) from e

    def run_pipeline(self):
        try:
            logging.info(">>> Training Pipeline Started.")
            TrainPipeline.is_pipeline_running = True

            data_ingestion_artifact: DataIngestionArtifact = self.start_data_ingestion()

            data_validation_artifact = self.start_data_validaton(
                data_ingestion_artifact=data_ingestion_artifact
            )
            data_transformation_artifact = self.start_data_transformation(
                data_validation_artifact=data_validation_artifact
            )
            model_trainer_artifact = self.start_model_trainer(
                data_transformation_artifact
            )
            model_evaluation_artifact = self.start_model_evaluation(
                data_validation_artifact, model_trainer_artifact
            )
            if not model_evaluation_artifact.is_model_accepted:
                raise Exception("The trained model is inefficient than the best model.")

            model_pusher_artifact = self.start_model_pusher(model_evaluation_artifact)

            TrainPipeline.is_pipeline_running = False
            self.sync_artifact_dir_to_s3()
            self.sync_saved_model_dir_to_s3()
            logging.info(">>> Training Pipeline Ended.")

        except Exception as e:
            self.sync_artifact_dir_to_s3()
            TrainPipeline.is_pipeline_running = False
            raise SensorException(e, sys) from e
