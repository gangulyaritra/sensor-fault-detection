import os
import sys
import shutil
from sensor.entity.artifact_entity import (
    ModelPusherArtifact,
    ModelEvaluationArtifact,
)
from sensor.entity.config_entity import ModelPusherConfig
from sensor.exception import SensorException
from sensor.logger import logging


class ModelPusher:
    """
    The Pusher component is used to push a validated model to
    a deployment target during model training or re-training.
    """

    def __init__(
        self,
        model_evaluation_artifact: ModelEvaluationArtifact,
        model_pusher_config: ModelPusherConfig,
    ):
        self.model_evaluation_artifact = model_evaluation_artifact
        self.model_pusher_config = model_pusher_config

    """
    A Pusher component consumes a trained model in SavedModel format 
    and produces the same SavedModel, along with versioning metadata.
    """

    def initiate_model_pusher(self) -> ModelPusherArtifact:
        try:
            logging.info(">> Model Pusher Component Started.")

            trained_model_path = self.model_evaluation_artifact.trained_model_path

            # Create a Model Pusher directory to save the model.
            model_file_path = self.model_pusher_config.model_file_path
            os.makedirs(os.path.dirname(model_file_path), exist_ok=True)
            shutil.copy(src=trained_model_path, dst=model_file_path)

            # Save Model Directory.
            saved_model_path = self.model_pusher_config.saved_model_path
            os.makedirs(os.path.dirname(saved_model_path), exist_ok=True)
            shutil.copy(src=trained_model_path, dst=saved_model_path)

            model_pusher_artifact = ModelPusherArtifact(
                saved_model_path=saved_model_path, model_file_path=model_file_path
            )

            logging.info(f"Model Pusher Artifact: [{model_pusher_artifact}].")
            logging.info(">> Model Pusher Component Ended.")
            return model_pusher_artifact

        except Exception as e:
            raise SensorException(e, sys) from e
