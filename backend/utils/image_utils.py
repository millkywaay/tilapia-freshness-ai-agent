import io
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

from config import IMAGE_SIZE, MAX_IMAGE_SIZE

def decode_image(
    file_bytes: bytes,
) -> np.ndarray:

    if not file_bytes:
        raise ValueError(
            "File gambar kosong."
        )

    if len(file_bytes) > MAX_IMAGE_SIZE:
        raise ValueError(
            "Ukuran gambar melebihi 10 MB."
        )

    try:

        with Image.open(
            io.BytesIO(file_bytes)
        ) as image:

            image = (
                ImageOps.exif_transpose(
                    image
                )
            )

            image = image.convert(
                "RGB"
            )

            image = image.resize(
                IMAGE_SIZE,
                Image.Resampling.BILINEAR,
            )

            image_array = np.asarray(
                image,
                dtype=np.float32,
            )

    except (
        UnidentifiedImageError,
        OSError,
        ValueError,
        Image.DecompressionBombError,
    ) as exc:

        raise ValueError(
            "File bukan gambar valid."
        ) from exc

    expected_shape = (
        IMAGE_SIZE[1],
        IMAGE_SIZE[0],
        3,
    )

    if (
        image_array.shape
        != expected_shape
    ):
        raise ValueError(
            f"Shape gambar "
            f"{image_array.shape}, "
            f"seharusnya "
            f"{expected_shape}."
        )

    return image_array


def preprocess_resnet(
    image_array: np.ndarray,
) -> np.ndarray:
    
    # 1. Reverse RGB to BGR
    processed = image_array[..., ::-1].copy()
    
    # 2. Subtract ImageNet mean (Caffe style, no scaling)
    mean = np.array([103.939, 116.779, 123.68], dtype=np.float32)
    processed -= mean

    return np.expand_dims(
        processed,
        axis=0,
    )
