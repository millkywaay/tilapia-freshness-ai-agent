import hashlib
import io
import logging
import math
import os
from dataclasses import dataclass
from typing import Optional

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

import tensorflow as tf
from tensorflow.keras.applications.resnet50 import (
    preprocess_input as resnet_preprocess,
)

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv
from openai import OpenAI


# =========================================================
# KONFIGURASI DASAR
# =========================================================

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("nilafresh")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "model")

IMAGE_SIZE = (224, 224)
CLASS_THRESHOLD = 0.5
MAX_IMAGE_SIZE = 10 * 1024 * 1024  # 10 MB

# Apabila dua model berbeda kelas, selisih vote di bawah nilai ini
# dianggap belum cukup kuat untuk memilih salah satu kelas.
MODEL_VOTE_MARGIN = 0.15

# Aturan veto pada penggabungan organ.
NONFRESH_VETO_CONFIDENCE = 0.85
NONFRESH_VETO_MARGIN = 0.10


def get_env_float(name: str, default: float) -> float:
    try:
        value = float(os.getenv(name, str(default)))
    except ValueError:
        logger.warning(
            "Nilai %s tidak valid. Menggunakan nilai default %.2f.",
            name,
            default,
        )
        value = default

    if value <= 0:
        logger.warning(
            "Nilai %s harus lebih besar dari 0. Menggunakan %.2f.",
            name,
            default,
        )
        return default

    return value


# Bobot ini sebaiknya diisi berdasarkan F1-score validation setiap model.
# Default 1.0 berarti performa kedua model dianggap setara.
MODEL_CONFIG = {
    "eyes": [
        {
            "name": "best_model_eyes",
            "filename": "best_model_eyes.keras",
            "reliability": get_env_float("EYES_BEST_WEIGHT", 1.0),
        },
        {
            "name": "model_eyes_resnet50",
            "filename": "model_eyes_resnet50.keras",
            "reliability": get_env_float("EYES_RESNET_WEIGHT", 1.0),
        },
    ],
    "gills": [
        {
            "name": "best_model_gills",
            "filename": "best_model_gills.keras",
            "reliability": get_env_float("GILLS_BEST_WEIGHT", 1.0),
        },
        {
            "name": "model_gills_resnet50",
            "filename": "model_gills_resnet50.keras",
            "reliability": get_env_float("GILLS_RESNET_WEIGHT", 1.0),
        },
    ],
}


# =========================================================
# FASTAPI
# =========================================================

app = FastAPI(
    title="NilaFresh API",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# STRUKTUR MODEL
# =========================================================

@dataclass
class LoadedModel:
    name: str
    filename: str
    reliability: float
    sha256: str
    model: tf.keras.Model


def calculate_sha256(file_path: str) -> str:
    """Menghitung checksum file tanpa memuat seluruh file ke memori."""

    digest = hashlib.sha256()

    with open(file_path, "rb") as model_file:
        while chunk := model_file.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()


def validate_model_shape(model: tf.keras.Model, model_name: str) -> None:
    input_shape = model.input_shape

    if isinstance(input_shape, list):
        input_shape = input_shape[0]

    if len(input_shape) != 4:
        raise ValueError(
            f"Model {model_name} memiliki input shape tidak valid: "
            f"{input_shape}"
        )

    height = input_shape[1]
    width = input_shape[2]
    channels = input_shape[3]

    if height not in (None, IMAGE_SIZE[1]):
        logger.warning(
            "Model %s menerima tinggi %s, sedangkan deployment memakai %s.",
            model_name,
            height,
            IMAGE_SIZE[1],
        )

    if width not in (None, IMAGE_SIZE[0]):
        logger.warning(
            "Model %s menerima lebar %s, sedangkan deployment memakai %s.",
            model_name,
            width,
            IMAGE_SIZE[0],
        )

    if channels not in (None, 3):
        raise ValueError(
            f"Model {model_name} tidak menerima citra RGB: {input_shape}"
        )


def load_model_group(organ: str) -> list[LoadedModel]:
    loaded_models: list[LoadedModel] = []
    loaded_checksums: set[str] = set()

    for config in MODEL_CONFIG[organ]:
        model_path = os.path.join(MODEL_DIR, config["filename"])

        if not os.path.isfile(model_path):
            logger.warning(
                "Model %s tidak ditemukan di %s.",
                config["name"],
                model_path,
            )
            continue

        checksum = calculate_sha256(model_path)

        # Menghindari file model identik dihitung dua kali.
        if checksum in loaded_checksums:
            logger.warning(
                "Model %s identik dengan model lain pada organ %s. "
                "Model dilewati agar tidak terjadi double voting.",
                config["name"],
                organ,
            )
            continue

        logger.info("Memuat model %s...", config["name"])

        model = tf.keras.models.load_model(
            model_path,
            compile=False,
        )

        validate_model_shape(model, config["name"])

        loaded_models.append(
            LoadedModel(
                name=config["name"],
                filename=config["filename"],
                reliability=config["reliability"],
                sha256=checksum,
                model=model,
            )
        )

        loaded_checksums.add(checksum)

    if not loaded_models:
        raise RuntimeError(
            f"Tidak ada model {organ} yang berhasil dimuat dari {MODEL_DIR}."
        )

    return loaded_models


MODELS = {
    "eyes": load_model_group("eyes"),
    "gills": load_model_group("gills"),
}


# =========================================================
# DEEPSEEK
# =========================================================

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

deepseek_client = (
    OpenAI(
        api_key=DEEPSEEK_API_KEY,
        base_url="https://api.deepseek.com",
    )
    if DEEPSEEK_API_KEY
    else None
)


# =========================================================
# PREPROCESSING
# =========================================================

def decode_image(file_bytes: bytes) -> np.ndarray:
    """
    Preprocessing yang sama dengan training ResNet50:

    1. Membaca gambar.
    2. Memperbaiki orientasi EXIF.
    3. Mengubah menjadi RGB.
    4. Resize menjadi 224 x 224 dengan bilinear.
    5. Mengubah menjadi float32.

    Fungsi resnet_preprocess dijalankan setelah tahap ini.
    """

    if not file_bytes:
        raise ValueError("File gambar kosong.")

    if len(file_bytes) > MAX_IMAGE_SIZE:
        raise ValueError("Ukuran file gambar melebihi 10 MB.")

    try:
        with Image.open(io.BytesIO(file_bytes)) as image:
            image = ImageOps.exif_transpose(image)
            image = image.convert("RGB")
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
        raise ValueError("File bukan gambar yang valid.") from exc

    expected_shape = (
        IMAGE_SIZE[1],
        IMAGE_SIZE[0],
        3,
    )

    if image_array.shape != expected_shape:
        raise ValueError(
            f"Shape gambar tidak valid: {image_array.shape}. "
            f"Shape yang diharapkan: {expected_shape}."
        )

    return image_array


def preprocess_resnet(image_array: np.ndarray) -> np.ndarray:
    """
    ResNet50 preprocess_input harus menerima nilai piksel 0-255,
    bukan gambar yang sudah dibagi 255.
    """

    processed = resnet_preprocess(image_array.copy())

    return np.expand_dims(
        processed,
        axis=0,
    )


# =========================================================
# PREDIKSI MODEL
# =========================================================

def normalize_probability(value: float) -> float:
    value = float(value)

    if not math.isfinite(value):
        raise ValueError(
            "Model menghasilkan nilai yang bukan bilangan finite."
        )

    # Toleransi kecil terhadap kesalahan floating point.
    if value < -1e-5 or value > 1.00001:
        raise ValueError(
            f"Output model berada di luar rentang probabilitas: {value}"
        )

    return min(max(value, 0.0), 1.0)


def extract_nonfresh_probability(raw_prediction) -> float:
    """
    Mendukung:
    - sigmoid satu output: [prob_nonfresh]
    - softmax dua output: [prob_fresh, prob_nonfresh]

    Berdasarkan mapping:
    0 = Fresh
    1 = NonFresh
    """

    if isinstance(raw_prediction, dict):
        raw_prediction = next(iter(raw_prediction.values()))

    if isinstance(raw_prediction, (list, tuple)):
        if not raw_prediction:
            raise ValueError("Model tidak menghasilkan output.")
        raw_prediction = raw_prediction[0]

    prediction_array = np.asarray(
        raw_prediction,
        dtype=np.float64,
    ).reshape(-1)

    if prediction_array.size == 1:
        probability = prediction_array[0]

    elif prediction_array.size == 2:
        probability = prediction_array[1]

    else:
        raise ValueError(
            "Output model harus berupa satu probabilitas sigmoid "
            "atau dua probabilitas softmax."
        )

    return normalize_probability(probability)


def predict_single_model(
    loaded_model: LoadedModel,
    processed_image: np.ndarray,
) -> dict:
    raw_prediction = loaded_model.model.predict(
        processed_image,
        verbose=0,
    )

    probability_nonfresh = extract_nonfresh_probability(
        raw_prediction
    )

    class_index = (
        1
        if probability_nonfresh >= CLASS_THRESHOLD
        else 0
    )

    class_confidence = (
        probability_nonfresh
        if class_index == 1
        else 1 - probability_nonfresh
    )

    # 0 berarti tepat pada threshold.
    # 1 berarti berada di ujung 0 atau 1.
    threshold_margin = min(
        abs(probability_nonfresh - CLASS_THRESHOLD) * 2,
        1.0,
    )

    # Model yang ragu-ragu tetap memiliki bobot kecil,
    # tetapi tidak mendominasi voting.
    effective_vote_weight = (
        loaded_model.reliability
        * max(threshold_margin, 0.05)
    )

    return {
        "name": loaded_model.name,
        "filename": loaded_model.filename,
        "prob_nonfresh": probability_nonfresh,
        "prob_fresh": 1 - probability_nonfresh,
        "class_index": class_index,
        "label": (
            "TIDAK SEGAR"
            if class_index == 1
            else "SEGAR"
        ),
        "confidence": class_confidence,
        "threshold_margin": threshold_margin,
        "reliability": loaded_model.reliability,
        "vote_weight": effective_vote_weight,
    }


# =========================================================
# ENSEMBLE PER ORGAN
# =========================================================

def ensemble_organ(
    loaded_models: list[LoadedModel],
    image_array: np.ndarray,
) -> dict:
    """
    Confidence-weighted hard voting.

    Tahapan:
    1. Setiap model menghasilkan probabilitas.
    2. Probabilitas diubah menjadi vote kelas menggunakan threshold 0.5.
    3. Vote dibobot menggunakan reliability model dan jarak dari threshold.
    4. Apabila vote terlalu seimbang, hasil organ dinyatakan tidak pasti.

    Penentuan kelas tidak menggunakan rata-rata probabilitas semata.
    """

    processed_image = preprocess_resnet(image_array)

    model_predictions = [
        predict_single_model(model, processed_image)
        for model in loaded_models
    ]

    fresh_vote = sum(
        prediction["vote_weight"]
        for prediction in model_predictions
        if prediction["class_index"] == 0
    )

    nonfresh_vote = sum(
        prediction["vote_weight"]
        for prediction in model_predictions
        if prediction["class_index"] == 1
    )

    total_vote = fresh_vote + nonfresh_vote

    if total_vote <= 0:
        raise ValueError("Total bobot voting model tidak valid.")

    vote_margin = (
        abs(nonfresh_vote - fresh_vote)
        / total_vote
    )

    model_labels = {
        prediction["class_index"]
        for prediction in model_predictions
    }

    if len(model_predictions) == 1:
        class_index: Optional[int] = model_predictions[0][
            "class_index"
        ]
        decision_method = "single_model"

    elif len(model_labels) == 1:
        class_index = next(iter(model_labels))
        decision_method = "unanimous_vote"

    elif vote_margin < MODEL_VOTE_MARGIN:
        class_index = None
        decision_method = "model_disagreement"

    else:
        class_index = (
            1
            if nonfresh_vote > fresh_vote
            else 0
        )
        decision_method = "confidence_weighted_vote"

    # Soft score hanya digunakan untuk tampilan persentase.
    # Penentuan kelas tetap menggunakan voting di atas.
    reliability_total = sum(
        prediction["reliability"]
        for prediction in model_predictions
    )

    weighted_prob_nonfresh = sum(
        prediction["prob_nonfresh"]
        * prediction["reliability"]
        for prediction in model_predictions
    ) / reliability_total

    if class_index is None:
        label = "PERLU PEMERIKSAAN LANJUTAN"
        confidence = 0.5

    else:
        label = (
            "TIDAK SEGAR"
            if class_index == 1
            else "SEGAR"
        )

        supporting_predictions = [
            prediction
            for prediction in model_predictions
            if prediction["class_index"] == class_index
        ]

        supporting_weight = sum(
            prediction["reliability"]
            for prediction in supporting_predictions
        )

        confidence = sum(
            prediction["confidence"]
            * prediction["reliability"]
            for prediction in supporting_predictions
        ) / supporting_weight

    return {
        "class_index": class_index,
        "label": label,
        "confidence": normalize_probability(confidence),
        "prob_nonfresh": normalize_probability(
            weighted_prob_nonfresh
        ),
        "prob_fresh": normalize_probability(
            1 - weighted_prob_nonfresh
        ),
        "fresh_vote": fresh_vote,
        "nonfresh_vote": nonfresh_vote,
        "vote_margin": vote_margin,
        "decision_method": decision_method,
        "models": model_predictions,
    }


# =========================================================
# PENGGABUNGAN MATA DAN INSANG
# =========================================================

def combine_organ_predictions(
    eye_result: dict,
    gill_result: dict,
) -> dict:
    """
    Penggabungan organ dengan aturan keputusan konservatif.

    Tidak menggunakan rata-rata probabilitas sebagai penentu kelas.
    """

    eye_class = eye_result["class_index"]
    gill_class = gill_result["class_index"]

    final_class: Optional[int]
    decision_reason: str

    # Keduanya memberikan kelas yang sama.
    if (
        eye_class is not None
        and eye_class == gill_class
    ):
        final_class = eye_class

        decision_reason = (
            "both_organs_nonfresh"
            if final_class == 1
            else "both_organs_fresh"
        )

    else:
        results = [eye_result, gill_result]

        nonfresh_results = [
            result
            for result in results
            if result["class_index"] == 1
        ]

        fresh_results = [
            result
            for result in results
            if result["class_index"] == 0
        ]

        strong_nonfresh = (
            max(
                nonfresh_results,
                key=lambda result: result["confidence"],
            )
            if nonfresh_results
            else None
        )

        strongest_fresh_confidence = max(
            (
                result["confidence"]
                for result in fresh_results
            ),
            default=0.0,
        )

        # Veto konservatif:
        # prediksi tidak segar harus sangat kuat dan lebih yakin
        # daripada prediksi segar.
        if (
            strong_nonfresh is not None
            and strong_nonfresh["confidence"]
            >= NONFRESH_VETO_CONFIDENCE
            and (
                strong_nonfresh["confidence"]
                - strongest_fresh_confidence
                >= NONFRESH_VETO_MARGIN
            )
        ):
            final_class = 1
            decision_reason = "strong_nonfresh_veto"

        else:
            final_class = None
            decision_reason = "organ_disagreement"

    # Worst-organ risk score.
    # Hanya dipakai sebagai informasi persentase,
    # bukan satu-satunya penentu label.
    final_prob_nonfresh = max(
        eye_result["prob_nonfresh"],
        gill_result["prob_nonfresh"],
    )

    if final_class == 1:
        final_label = "TIDAK SEGAR"

        nonfresh_confidences = [
            result["confidence"]
            for result in (eye_result, gill_result)
            if result["class_index"] == 1
        ]

        final_confidence = (
            min(nonfresh_confidences)
            if decision_reason == "both_organs_nonfresh"
            else max(nonfresh_confidences)
        )

    elif final_class == 0:
        final_label = "SEGAR"

        # Menggunakan confidence terendah agar kesimpulan
        # segar tidak terlalu optimistis.
        final_confidence = min(
            eye_result["confidence"],
            gill_result["confidence"],
        )

    else:
        final_label = "PERLU PEMERIKSAAN LANJUTAN"
        final_confidence = 0.5

    return {
        "eye": eye_result,
        "gill": gill_result,
        "final": {
            "class_index": final_class,
            "label": final_label,
            "confidence": normalize_probability(
                final_confidence
            ),
            "decision_reason": decision_reason,
        },
        "final_prob_nonfresh": normalize_probability(
            final_prob_nonfresh
        ),
        "ensemble_method": (
            "confidence_weighted_hard_voting"
            "_and_conservative_organ_fusion"
        ),
    }


# =========================================================
# HELPER TAMPILAN
# =========================================================

def get_confidence_level(confidence: float) -> str:
    if confidence >= 0.90:
        return "Sangat Tinggi"
    if confidence >= 0.80:
        return "Tinggi"
    if confidence >= 0.70:
        return "Sedang"
    return "Rendah"


# =========================================================
# DEEPSEEK EXPLANATION
# =========================================================

def get_deepseek_explanation(
    label: str,
    confidence_percent: float,
    fresh_eye_percent: float,
    fresh_gill_percent: float,
    fresh_final_percent: float,
    nonfresh_eye_percent: float,
    nonfresh_gill_percent: float,
    nonfresh_final_percent: float,
    confidence_level: str,
    decision_reason: str,
) -> str:
    if deepseek_client is None:
        raise RuntimeError(
            "DEEPSEEK_API_KEY belum dikonfigurasi."
        )

    status = label.lower()

    if label == "SEGAR":
        score_info = f"""
- Status ikan: {status}
- Skor kesegaran mata: {fresh_eye_percent:.2f}%
- Skor kesegaran insang: {fresh_gill_percent:.2f}%
- Skor kesegaran akhir: {fresh_final_percent:.2f}%
- Keyakinan sistem: {confidence_percent:.2f}% ({confidence_level})
- Dasar keputusan: kedua organ mendukung status segar
"""

    elif label == "TIDAK SEGAR":
        score_info = f"""
- Status ikan: {status}
- Skor ketidaksegaran mata: {nonfresh_eye_percent:.2f}%
- Skor ketidaksegaran insang: {nonfresh_gill_percent:.2f}%
- Skor risiko akhir: {nonfresh_final_percent:.2f}%
- Keyakinan sistem: {confidence_percent:.2f}% ({confidence_level})
- Dasar keputusan: {decision_reason}
"""

    else:
        score_info = f"""
- Status ikan: {status}
- Skor kesegaran mata: {fresh_eye_percent:.2f}%
- Skor kesegaran insang: {fresh_gill_percent:.2f}%
- Skor ketidaksegaran mata: {nonfresh_eye_percent:.2f}%
- Skor ketidaksegaran insang: {nonfresh_gill_percent:.2f}%
- Keyakinan sistem: {confidence_percent:.2f}% ({confidence_level})
- Dasar keputusan: hasil model atau hasil kedua organ belum konsisten
"""

    prompt = f"""
Kamu adalah AI Fish Freshness Assistant yang menjelaskan hasil
deteksi kesegaran ikan nila berdasarkan citra mata dan insang.

Informasi hasil deteksi:
{score_info}

Instruksi:
1. Gunakan Bahasa Indonesia yang formal, jelas, dan mudah dipahami.
2. Jangan mengarang ciri visual yang tidak diberikan oleh sistem.
3. Jelaskan hubungan hasil mata, insang, dan kesimpulan akhir.
4. Berikan rekomendasi praktis dan aman.
5. Gunakan tepat tiga paragraf pendek:
Kondisi organ: ...
Kesimpulan: ...
Rekomendasi: ...
6. Panjang keseluruhan 70-110 kata.
7. Jangan memberikan jaminan keamanan pangan hanya dari citra.
8. Jangan menyebut CNN, ResNet, probabilitas, dataset, atau machine learning.
9. Jangan menggunakan pembuka seperti "Tentu", "Baik", atau "Berikut".
10. Berikan hanya hasil analisis tanpa judul atau bullet.
"""

    response = deepseek_client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        temperature=0.3,
        max_tokens=260,
    )

    return response.choices[0].message.content.strip()


# =========================================================
# ENDPOINT
# =========================================================

@app.get("/")
def root():
    return {
        "status": "NilaFresh API is running",
        "version": "2.0.0",
        "ensemble_method": (
            "confidence-weighted hard voting "
            "+ conservative organ fusion"
        ),
        "models": {
            organ: [
                {
                    "name": model.name,
                    "filename": model.filename,
                    "reliability": model.reliability,
                    "sha256": model.sha256[:12],
                }
                for model in models
            ]
            for organ, models in MODELS.items()
        },
    }


@app.post("/predict")
async def predict(
    eye_image: UploadFile = File(...),
    gill_image: UploadFile = File(...),
):
    try:
        eye_bytes = await eye_image.read()
        gill_bytes = await gill_image.read()

        eye_array = decode_image(eye_bytes)
        gill_array = decode_image(gill_bytes)

        eye_result = ensemble_organ(
            MODELS["eyes"],
            eye_array,
        )

        gill_result = ensemble_organ(
            MODELS["gills"],
            gill_array,
        )

        prediction = combine_organ_predictions(
            eye_result,
            gill_result,
        )

    except (
        OSError,
        ValueError,
        IndexError,
        tf.errors.OpError,
    ) as exc:
        logger.exception("Prediksi gagal.")

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    final_label = prediction["final"]["label"]
    final_confidence = prediction["final"]["confidence"]
    final_prob_nonfresh = prediction["final_prob_nonfresh"]

    confidence_percent = final_confidence * 100
    confidence_level = get_confidence_level(
        final_confidence
    )

    prob_nonfresh_eyes = eye_result["prob_nonfresh"]
    prob_nonfresh_gills = gill_result["prob_nonfresh"]

    fresh_eye_percent = (
        1 - prob_nonfresh_eyes
    ) * 100

    fresh_gill_percent = (
        1 - prob_nonfresh_gills
    ) * 100

    fresh_final_percent = (
        1 - final_prob_nonfresh
    ) * 100

    nonfresh_eye_percent = (
        prob_nonfresh_eyes
    ) * 100

    nonfresh_gill_percent = (
        prob_nonfresh_gills
    ) * 100

    nonfresh_final_percent = (
        final_prob_nonfresh
    ) * 100

    try:
        explanation = get_deepseek_explanation(
            label=final_label,
            confidence_percent=confidence_percent,
            fresh_eye_percent=fresh_eye_percent,
            fresh_gill_percent=fresh_gill_percent,
            fresh_final_percent=fresh_final_percent,
            nonfresh_eye_percent=nonfresh_eye_percent,
            nonfresh_gill_percent=nonfresh_gill_percent,
            nonfresh_final_percent=nonfresh_final_percent,
            confidence_level=confidence_level,
            decision_reason=prediction["final"][
                "decision_reason"
            ],
        )

    except Exception:
        logger.exception(
            "DeepSeek gagal. Menggunakan fallback."
        )

        explanation = (
            "Kondisi organ: Citra mata dan insang telah dianalisis "
            "secara terpisah menggunakan beberapa hasil prediksi.\n"
            f"Kesimpulan: Sistem menghasilkan status "
            f"{final_label.lower()} dengan tingkat keyakinan "
            f"{confidence_percent:.1f}%.\n"
            "Rekomendasi: Gunakan hasil sebagai informasi pendukung "
            "dan tetap periksa aroma, tekstur, warna, serta kondisi "
            "fisik ikan sebelum dikonsumsi."
        )

    return {
        "eye": {
            "label": eye_result["label"],
            "confidence": round(
                eye_result["confidence"],
                4,
            ),
            "prob_nonfresh": round(
                eye_result["prob_nonfresh"],
                4,
            ),
            "decision_method": eye_result[
                "decision_method"
            ],
            "vote_margin": round(
                eye_result["vote_margin"],
                4,
            ),
            "models": [
                {
                    "name": item["name"],
                    "label": item["label"],
                    "prob_nonfresh": round(
                        item["prob_nonfresh"],
                        4,
                    ),
                    "confidence": round(
                        item["confidence"],
                        4,
                    ),
                    "reliability": round(
                        item["reliability"],
                        4,
                    ),
                    "vote_weight": round(
                        item["vote_weight"],
                        4,
                    ),
                }
                for item in eye_result["models"]
            ],
        },

        "gill": {
            "label": gill_result["label"],
            "confidence": round(
                gill_result["confidence"],
                4,
            ),
            "prob_nonfresh": round(
                gill_result["prob_nonfresh"],
                4,
            ),
            "decision_method": gill_result[
                "decision_method"
            ],
            "vote_margin": round(
                gill_result["vote_margin"],
                4,
            ),
            "models": [
                {
                    "name": item["name"],
                    "label": item["label"],
                    "prob_nonfresh": round(
                        item["prob_nonfresh"],
                        4,
                    ),
                    "confidence": round(
                        item["confidence"],
                        4,
                    ),
                    "reliability": round(
                        item["reliability"],
                        4,
                    ),
                    "vote_weight": round(
                        item["vote_weight"],
                        4,
                    ),
                }
                for item in gill_result["models"]
            ],
        },

        "final": {
            "label": final_label,
            "confidence": round(
                final_confidence,
                4,
            ),
            "decision_reason": prediction[
                "final"
            ]["decision_reason"],
        },

        "ensemble_method": prediction[
            "ensemble_method"
        ],

        # Field lama tetap tersedia agar frontend tidak rusak.
        "label": final_label,
        "confidence": round(
            final_confidence,
            4,
        ),
        "confidence_percent": round(
            confidence_percent,
            2,
        ),
        "confidence_level": confidence_level,

        "fresh_eye_percent": round(
            fresh_eye_percent,
            2,
        ),
        "fresh_gill_percent": round(
            fresh_gill_percent,
            2,
        ),
        "fresh_final_percent": round(
            fresh_final_percent,
            2,
        ),

        "nonfresh_eye_percent": round(
            nonfresh_eye_percent,
            2,
        ),
        "nonfresh_gill_percent": round(
            nonfresh_gill_percent,
            2,
        ),
        "nonfresh_final_percent": round(
            nonfresh_final_percent,
            2,
        ),

        "prob_nonfresh_eyes": round(
            prob_nonfresh_eyes,
            4,
        ),
        "prob_nonfresh_gills": round(
            prob_nonfresh_gills,
            4,
        ),
        "final_prob_nonfresh": round(
            final_prob_nonfresh,
            4,
        ),

        "explanation": explanation,
    }