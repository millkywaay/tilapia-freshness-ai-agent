import os
import hashlib
import logging
import tensorflow as tf
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


def validate_model_shape(
    model: tf.keras.Model,
    model_name: str,
) -> None:

    input_shape = model.input_shape

    if isinstance(
        input_shape,
        list,
    ):
        input_shape = input_shape[0]

    if len(input_shape) != 4:
        raise ValueError(
            f"Input shape model "
            f"{model_name} tidak valid: "
            f"{input_shape}"
        )

    height = input_shape[1]
    width = input_shape[2]
    channels = input_shape[3]

    if height not in (
        None,
        IMAGE_SIZE[1],
    ):
        logger.warning(
            "%s menerima height %s, "
            "deployment menggunakan %s.",
            model_name,
            height,
            IMAGE_SIZE[1],
        )

    if width not in (
        None,
        IMAGE_SIZE[0],
    ):
        logger.warning(
            "%s menerima width %s, "
            "deployment menggunakan %s.",
            model_name,
            width,
            IMAGE_SIZE[0],
        )

    if channels not in (
        None,
        3,
    ):
        raise ValueError(
            f"Model {model_name} "
            f"tidak menerima RGB: "
            f"{input_shape}"
        )


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
        "Memuat model final %s: %s",
        organ,
        filename,
    )

    model = (
        tf.keras.models.load_model(
            model_path,
            compile=False,
        )
    )

    validate_model_shape(
        model,
        organ,
    )

    return {
        "organ": organ,
        "filename": filename,
        "sha256": calculate_sha256(
            model_path
        ),
        "model": model,
    }


MODELS = {
    "eyes": load_final_model(
        "eyes"
    ),
    "gills": load_final_model(
        "gills"
    ),
}
