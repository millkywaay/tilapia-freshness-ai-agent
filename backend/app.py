import os
import io
import math
import numpy as np
from PIL import Image

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from openai import OpenAI
from dotenv import load_dotenv

import tensorflow as tf
from tensorflow.keras.applications.resnet50 import preprocess_input as resnet_preprocess


load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Load model ────────────────────────────────────────────────────────
BASE_DIR = os.path.dirname(__file__)

model_eyes = tf.keras.models.load_model(
    os.path.join(BASE_DIR, "model/model_eyes_resnet50.keras")
)

model_gills = tf.keras.models.load_model(
    os.path.join(BASE_DIR, "model/model_gills_resnet50.keras")
)


# ── DeepSeek client ───────────────────────────────────────────────────
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)


# ── Helper preprocessing ──────────────────────────────────────────────
def preprocess_image(file_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    img = img.resize((224, 224), Image.BILINEAR)

    arr = np.array(img, dtype=np.float32)
    arr = resnet_preprocess(arr)

    return np.expand_dims(arr, axis=0)


# ── Helper confidence level ───────────────────────────────────────────
def get_confidence_level(confidence: float) -> str:
    if confidence >= 0.90:
        return "Sangat Tinggi"
    elif confidence >= 0.80:
        return "Tinggi"
    elif confidence >= 0.70:
        return "Sedang"
    else:
        return "Rendah"


def normalize_probability(value: float) -> float:
    """Return a finite probability in the inclusive 0..1 range."""
    value = float(value)
    if not math.isfinite(value):
        raise ValueError("Model menghasilkan probabilitas yang tidak valid.")
    return min(max(value, 0.0), 1.0)


def build_prediction_result(
    prob_nonfresh_eyes: float,
    prob_nonfresh_gills: float,
) -> dict:
    """Apply the same explicit freshness rules to both organ predictions."""
    eye_nonfresh = prob_nonfresh_eyes >= 0.5
    gill_nonfresh = prob_nonfresh_gills >= 0.5
    eye_confidence = prob_nonfresh_eyes if eye_nonfresh else 1 - prob_nonfresh_eyes
    gill_confidence = prob_nonfresh_gills if gill_nonfresh else 1 - prob_nonfresh_gills
    final_prob_nonfresh = (prob_nonfresh_eyes + prob_nonfresh_gills) / 2
    predictions_disagree = eye_nonfresh != gill_nonfresh
    ensemble_confidence = max(final_prob_nonfresh, 1 - final_prob_nonfresh)
    disagreement_has_low_confidence = min(eye_confidence, gill_confidence) < 0.70

    if predictions_disagree and disagreement_has_low_confidence:
        final_label = "PERLU PEMERIKSAAN LANJUTAN"
        final_confidence = ensemble_confidence
    elif eye_nonfresh or gill_nonfresh:
        final_label = "TIDAK SEGAR"
        final_confidence = final_prob_nonfresh
    else:
        final_label = "SEGAR"
        final_confidence = 1 - final_prob_nonfresh

    return {
        "eye": {
            "label": "TIDAK SEGAR" if eye_nonfresh else "SEGAR",
            "confidence": eye_confidence,
        },
        "gill": {
            "label": "TIDAK SEGAR" if gill_nonfresh else "SEGAR",
            "confidence": gill_confidence,
        },
        "final": {
            "label": final_label,
            "confidence": final_confidence,
        },
        "final_prob_nonfresh": final_prob_nonfresh,
    }

# ── Helper DeepSeek Explanation / AI Agent ────────────────────────────
def get_deepseek_explanation(
    label: str,
    confidence_percent: float,
    fresh_eye_percent: float,
    fresh_gill_percent: float,
    fresh_final_percent: float,
    nonfresh_eye_percent: float,
    nonfresh_gill_percent: float,
    nonfresh_final_percent: float,
    confidence_level: str
) -> str:

    status = label.lower()

    if label == "SEGAR":
        score_info = f"""
- Status ikan: {status}
- Tingkat kesegaran mata: {fresh_eye_percent:.2f}%
- Tingkat kesegaran insang: {fresh_gill_percent:.2f}%
- Tingkat kesegaran akhir: {fresh_final_percent:.2f}%
- Keyakinan sistem: {confidence_percent:.2f}% ({confidence_level})
"""
    elif label == "TIDAK SEGAR":
        score_info = f"""
- Status ikan: {status}
- Tingkat ketidaksegaran mata: {nonfresh_eye_percent:.2f}%
- Tingkat ketidaksegaran insang: {nonfresh_gill_percent:.2f}%
- Tingkat ketidaksegaran akhir: {nonfresh_final_percent:.2f}%
- Keyakinan sistem: {confidence_percent:.2f}% ({confidence_level})
"""
    else:
        score_info = f"""
- Status ikan: {status}
- Tingkat kesegaran mata: {fresh_eye_percent:.2f}%
- Tingkat kesegaran insang: {fresh_gill_percent:.2f}%
- Keyakinan sistem: {confidence_percent:.2f}% ({confidence_level})
"""

    prompt = f"""
Kamu adalah AI Fish Freshness Assistant yang bertugas menjelaskan hasil deteksi kesegaran ikan nila berdasarkan citra mata dan insang.

Informasi hasil deteksi:
{score_info}

Instruksi:
1. Gunakan Bahasa Indonesia yang formal, jelas, dan mudah dipahami.
2. Jelaskan kondisi mata dan insang berdasarkan skor yang tersedia tanpa mengarang ciri visual yang tidak diberikan.
3. Jelaskan bagaimana kedua hasil organ mendukung atau berbeda dari kesimpulan akhir.
4. Berikan rekomendasi praktis: layak dipertimbangkan untuk dikonsumsi, perlu pemeriksaan sensorik lanjutan, atau sebaiknya tidak dikonsumsi.
5. Gunakan tepat tiga paragraf pendek dengan format berikut:
Kondisi organ: [penjelasan mata dan insang]
Kesimpulan: [makna hasil gabungan dan tingkat keyakinan]
Rekomendasi: [tindakan praktis dan aman]
6. Panjang keseluruhan 70-110 kata agar informatif tetapi tetap ringkas.
7. Jangan memberikan jaminan keamanan pangan hanya berdasarkan hasil citra.
8. Jangan menyebut istilah teknis seperti model AI, CNN, ResNet, probabilitas, dataset, atau machine learning.
9. Jangan menggunakan kata pembuka seperti "Tentu", "Baik", "Berikut", atau sejenisnya.
10. Berikan hanya hasil analisis tanpa judul tambahan atau bullet.
"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3,
        max_tokens=260
    )

    return response.choices[0].message.content.strip()


# ── Endpoint ──────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "status": "NilaFresh API is running"
    }


@app.post("/predict")
async def predict(
    eye_image: UploadFile = File(...),
    gill_image: UploadFile = File(...)
):
    try:
        eye_bytes = await eye_image.read()
        gill_bytes = await gill_image.read()
        eye_arr = preprocess_image(eye_bytes)
        gill_arr = preprocess_image(gill_bytes)

        # Output sigmoid diasumsikan sebagai probabilitas NonFresh.
        prob_nonfresh_eyes = normalize_probability(
            model_eyes.predict(eye_arr, verbose=0)[0][0]
        )
        prob_nonfresh_gills = normalize_probability(
            model_gills.predict(gill_arr, verbose=0)[0][0]
        )
    except (OSError, ValueError, IndexError) as exc:
        raise HTTPException(
            status_code=422,
            detail="Gambar tidak dapat diproses atau hasil model tidak valid.",
        ) from exc

    prediction = build_prediction_result(
        prob_nonfresh_eyes,
        prob_nonfresh_gills,
    )
    final_prob_nonfresh = prediction["final_prob_nonfresh"]
    label = prediction["final"]["label"]
    confidence = prediction["final"]["confidence"]

    confidence_percent = confidence * 100
    confidence_level = get_confidence_level(confidence)

    fresh_eye_percent = (1 - prob_nonfresh_eyes) * 100
    fresh_gill_percent = (1 - prob_nonfresh_gills) * 100
    fresh_final_percent = (1 - final_prob_nonfresh) * 100

    nonfresh_eye_percent = prob_nonfresh_eyes * 100
    nonfresh_gill_percent = prob_nonfresh_gills * 100
    nonfresh_final_percent = final_prob_nonfresh * 100

    try:
        explanation = get_deepseek_explanation(
            label=label,
            confidence_percent=confidence_percent,
            fresh_eye_percent=fresh_eye_percent,
            fresh_gill_percent=fresh_gill_percent,
            fresh_final_percent=fresh_final_percent,
            nonfresh_eye_percent=nonfresh_eye_percent,
            nonfresh_gill_percent=nonfresh_gill_percent,
            nonfresh_final_percent=nonfresh_final_percent,
            confidence_level=confidence_level,
        )
    except Exception:
        explanation = (
            "Kondisi organ: Prediksi mata dan insang telah diproses secara terpisah berdasarkan citra yang diunggah.\n"
            f"Kesimpulan: Hasil gabungan menunjukkan status {label.lower()} dengan tingkat keyakinan {confidence_percent:.1f}%.\n"
            "Rekomendasi: Gunakan hasil ini sebagai informasi pendukung dan tetap periksa aroma, tekstur, serta kondisi fisik ikan sebelum dikonsumsi."
        )

    return {
        "eye": {
            "label": prediction["eye"]["label"],
            "confidence": round(prediction["eye"]["confidence"], 4),
        },
        "gill": {
            "label": prediction["gill"]["label"],
            "confidence": round(prediction["gill"]["confidence"], 4),
        },
        "final": {
            "label": prediction["final"]["label"],
            "confidence": round(prediction["final"]["confidence"], 4),
        },

        # Field datar dipertahankan untuk kompatibilitas dengan klien lama.
        "label": label,
        "confidence": round(confidence, 4),
        "confidence_percent": round(confidence_percent, 2),
        "confidence_level": confidence_level,

        "fresh_eye_percent": round(fresh_eye_percent, 2),
        "fresh_gill_percent": round(fresh_gill_percent, 2),
        "fresh_final_percent": round(fresh_final_percent, 2),

        "nonfresh_eye_percent": round(nonfresh_eye_percent, 2),
        "nonfresh_gill_percent": round(nonfresh_gill_percent, 2),
        "nonfresh_final_percent": round(nonfresh_final_percent, 2),

        "prob_nonfresh_eyes": round(prob_nonfresh_eyes, 4),
        "prob_nonfresh_gills": round(prob_nonfresh_gills, 4),
        "final_prob_nonfresh": round(final_prob_nonfresh, 4),

        "explanation": explanation
    }
