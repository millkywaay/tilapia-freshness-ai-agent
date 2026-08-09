import os
import hashlib
import logging
import ai_edge_litert.interpreter as tflite
from config import MODEL_DIR, MODEL_FILES, IMAGE_SIZE

logger = logging.getLogger("nilafresh")

def calculate_sha256(
    file_path: str,
) -> str:

    digest = hashlib.sha256()

    with open(
        file_path,
        "rb",
    ) as model_file:

        while chunk := model_file.read(
            1024 * 1024
        ):
            digest.update(chunk)

    return digest.hexdigest()





def load_final_model(
    organ: str,
) -> dict:

    filename = MODEL_FILES[organ]

    model_path = os.path.join(
        MODEL_DIR,
        filename,
    )

    if not os.path.isfile(
        model_path
    ):
        raise RuntimeError(
            f"Model {organ} "
            f"tidak ditemukan:\n"
            f"{model_path}"
        )

    logger.info(
        "Memuat TFLite model %s: %s",
        organ,
        filename,
    )

    interpreter = tflite.Interpreter(model_path=model_path)
    interpreter.allocate_tensors()

    return {
        "organ": organ,
        "filename": filename,
        "sha256": calculate_sha256(
            model_path
        ),
        "model": interpreter,
    }


MODELS = {
    "eyes": load_final_model(
        "eyes"
    ),
    "gills": load_final_model(
        "gills"
    ),
}
