import os
import io
import numpy as np
from PIL import Image
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from dotenv import load_dotenv
import tensorflow as tf

load_dotenv()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Load model ────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(__file__)
model_eyes  = tf.keras.models.load_model(os.path.join(BASE_DIR, "model/best_model_eyes.keras"))
model_gills = tf.keras.models.load_model(os.path.join(BASE_DIR, "model/best_model_gills.keras"))

# ── DeepSeek client ───────────────────────────────────────────────────
client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com"
)

# ── Helper ────────────────────────────────────────────────────────────
def preprocess_image(file_bytes: bytes) -> np.ndarray:
    img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
    img = img.resize((224, 224), Image.BILINEAR)
    arr = np.array(img, dtype=np.float32)
    # MobileNetV2 preprocess: skala ke [-1, 1]
    arr = (arr / 127.5) - 1.0
    return np.expand_dims(arr, axis=0)

def get_deepseek_explanation(label: str, confidence: float) -> str:
    status = "segar" if label == "Fresh" else "tidak segar"
    prompt = f"""Kamu adalah asisten ahli kualitas ikan. Jelaskan dalam Bahasa Indonesia 
    kondisi ikan Nila yang {status}  berdasarkan ciri mata dan insangnya. 
    Jangan gunakan kata pembuka seperti "Tentu", "Baik", atau sejenisnya. 
    Langsung ke penjelasan. Maksimal 3 kalimat."""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300
    )
    return response.choices[0].message.content
# ── Endpoint ──────────────────────────────────────────────────────────
@app.get("/")
def root():
    return {"status": "NilaFresh API is running"}

@app.post("/predict")
async def predict(
    eye_image:  UploadFile = File(...),
    gill_image: UploadFile = File(...)
):
    eye_bytes  = await eye_image.read()
    gill_bytes = await gill_image.read()

    eye_arr  = preprocess_image(eye_bytes)
    gill_arr = preprocess_image(gill_bytes)

    prob_eyes  = float(model_eyes.predict(eye_arr,   verbose=0)[0][0])
    prob_gills = float(model_gills.predict(gill_arr, verbose=0)[0][0])
    final_prob = (prob_eyes + prob_gills) / 2

    label      = "NonFresh" if final_prob >= 0.5 else "Fresh"
    confidence = final_prob if final_prob >= 0.5 else 1 - final_prob

    explanation = get_deepseek_explanation(label, confidence)

    return {
        "label"      : label,
        "confidence" : round(confidence, 4),
        "prob_eyes"  : round(prob_eyes,  4),
        "prob_gills" : round(prob_gills, 4),
        "final_prob" : round(final_prob, 4),
        "explanation": explanation
    }