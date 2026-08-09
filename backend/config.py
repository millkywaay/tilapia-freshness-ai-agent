import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")

IMAGE_SIZE = (224, 224)
MAX_IMAGE_SIZE = 10 * 1024 * 1024

CLASS_THRESHOLD = float(
    os.getenv("CLASS_THRESHOLD", "0.5")
)

NONFRESH_VETO_CONFIDENCE = float(
    os.getenv(
        "NONFRESH_VETO_CONFIDENCE",
        "0.85"
    )
)

MODEL_FILES = {
    "eyes": os.getenv(
        "EYES_MODEL_FILE",
        "best_model_eyes.keras",
    ),
    "gills": os.getenv(
        "GILLS_MODEL_FILE",
        "best_model_gills.keras",
    ),
}
