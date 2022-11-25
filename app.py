import os
import pandas as pd
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from starlette.responses import RedirectResponse
from uvicorn import run as app_run

from sensor.pipeline.train_pipeline import TrainPipeline
from sensor.utils import read_yaml_file, load_object
from sensor.ml.model.estimator import ModelResolver, TargetValueMapping
from sensor.constant.training_pipeline import SAVED_MODEL_DIR, SCHEMA_FILE_PATH
from sensor.logger import logging


env_file_path = os.path.join(os.getcwd(), "env.yaml")


def set_env_variable(env_file_path):
    if os.getenv("MONGO_DB_URL", None) is None:
        env_config = read_yaml_file(env_file_path)
        os.environ["MONGO_DB_URL"] = env_config["MONGO_DB_URL"]


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["authentication"])
async def index():
    return RedirectResponse(url="/docs")


@app.get("/train")
async def train_route():
    try:
        train_pipeline = TrainPipeline()
        if train_pipeline.is_pipeline_running:
            return Response("The training pipeline is already running.")
        train_pipeline.run_pipeline()
        return Response("Training Done Successfully.")

    except Exception as e:
        return Response(f"Error Occurred! {e}")


@app.get("/predict")
async def predict_route(datafile: UploadFile = File(Ellipsis)):
    try:
        # Read Prediction CSV File.
        df = pd.read_csv(datafile.file)

        # Drop Specified Columns.
        schema_config = read_yaml_file(SCHEMA_FILE_PATH)
        df = df.drop(schema_config["drop_columns"], axis=1)

        # Load Model.
        model_resolver = ModelResolver(model_dir=SAVED_MODEL_DIR)
        if not model_resolver.is_model_exists():
            return Response("Model is Unavailable.")

        best_model_path = model_resolver.get_best_model_path()
        model = load_object(file_path=best_model_path)
        y_pred = model.predict(df)

        df["predicted_class"] = y_pred
        df["predicted_class"].replace(
            TargetValueMapping().reverse_mapping(), inplace=True
        )
        df.to_html()
        return Response("Prediction Done Successfully.")

    except Exception as e:
        return Response(f"Error Occurred! {e}")


def main():
    try:
        set_env_variable(env_file_path)
        training_pipeline = TrainPipeline()
        training_pipeline.run_pipeline()
    except Exception as e:
        logging.exception(e)


if __name__ == "__main__":
    app_run(app, host="0.0.0.0", port=8080)
