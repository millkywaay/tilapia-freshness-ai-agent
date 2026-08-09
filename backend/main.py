import logging


from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from config import NONFRESH_VETO_CONFIDENCE
from utils.image_utils import decode_image
from services.model_service import MODELS
from services.predict_service import predict_organ
from services.fusion_service import fuse_predictions
from services.deepseek_service import deepseek_client, get_deepseek_explanation, get_confidence_level

logger = logging.getLogger("nilafresh")

app = FastAPI(
    title="NilaFresh API",
    version="3.0.0",
    description=(
        "Deteksi kesegaran ikan nila menggunakan "
        "model mata dan insang dengan "
        "Conservative Decision-Level Late Fusion."
    ),
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():

    return {

        "status": (
            "NilaFresh API "
            "is running"
        ),

        "version": "3.0.0",

        "fusion_method": (
            "conservative_decision_level_"
            "late_fusion"
        ),

        "fusion_config": {

            "nonfresh_veto_confidence": (
                NONFRESH_VETO_CONFIDENCE
            ),
        },

        "models": {

            organ: {

                "filename": (
                    model["filename"]
                ),

                "sha256": (
                    model["sha256"][:12]
                ),
            }

            for organ, model
            in MODELS.items()
        },
    }


@app.get("/health")
def health():

    return {

        "status": "ok",

        "eyes_model_loaded": (
            MODELS["eyes"]["model"]
            is not None
        ),

        "gills_model_loaded": (
            MODELS["gills"]["model"]
            is not None
        ),

        "deepseek_configured": (
            deepseek_client
            is not None
        ),
    }


@app.post("/predict")
async def predict(

    eye_image: UploadFile = File(...),
    gill_image: UploadFile = File(...),

):

    try:

        eye_bytes = (
            await eye_image.read()
        )

        gill_bytes = (
            await gill_image.read()
        )

        eye_array = (
            decode_image(
                eye_bytes
            )
        )

        gill_array = (
            decode_image(
                gill_bytes
            )
        )

        eye_result = (
            predict_organ(
                MODELS["eyes"],
                eye_array,
            )
        )

        gill_result = (
            predict_organ(
                MODELS["gills"],
                gill_array,
            )
        )

        prediction = (
            fuse_predictions(
                eye_result,
                gill_result,
            )
        )

    except (
        OSError,
        ValueError,
        IndexError,
        Exception,
    ) as exc:

        logger.exception(
            "Prediksi gagal."
        )

        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc


    # =====================================================
    # RESULT
    # =====================================================

    final_label = (
        prediction[
            "final"
        ]["label"]
    )

    final_confidence = (
        prediction[
            "final"
        ]["confidence"]
    )

    final_prob_nonfresh = (
        prediction[
            "final_prob_nonfresh"
        ]
    )

    final_prob_fresh = (
        prediction[
            "final_prob_fresh"
        ]
    )


    # =====================================================
    # PERCENTAGE
    # =====================================================

    confidence_percent = (
        final_confidence
        * 100
    )

    confidence_level = (
        get_confidence_level(
            final_confidence
        )
    )

    prob_nonfresh_eyes = (
        eye_result[
            "prob_nonfresh"
        ]
    )

    prob_nonfresh_gills = (
        gill_result[
            "prob_nonfresh"
        ]
    )

    fresh_eye_percent = (
        (
            1
            - prob_nonfresh_eyes
        )
        * 100
    )

    fresh_gill_percent = (
        (
            1
            - prob_nonfresh_gills
        )
        * 100
    )

    fresh_final_percent = (
        final_prob_fresh
        * 100
    )

    nonfresh_eye_percent = (
        prob_nonfresh_eyes
        * 100
    )

    nonfresh_gill_percent = (
        prob_nonfresh_gills
        * 100
    )

    nonfresh_final_percent = (
        final_prob_nonfresh
        * 100
    )


    # =====================================================
    # DEEPSEEK
    # =====================================================

    try:

        explanation = (
            get_deepseek_explanation(

                label=final_label,

                confidence_percent=(
                    confidence_percent
                ),

                eye_label=(
                    eye_result["label"]
                ),

                eye_confidence_percent=(
                    eye_result["confidence"] * 100
                ),

                gill_label=(
                    gill_result["label"]
                ),

                gill_confidence_percent=(
                    gill_result["confidence"] * 100
                ),

                decision_reason=(
                    prediction[
                        "final"
                    ][
                        "decision_reason"
                    ]
                ),
            )
        )

    except Exception:

        logger.exception(
            "DeepSeek gagal. "
            "Menggunakan fallback."
        )

        explanation = f"""
**Analisis Organ**
• Kondisi mata: {eye_result['label'].lower()} dengan keyakinan {eye_result['confidence']*100:.1f}%.
• Kondisi insang: {gill_result['label'].lower()} dengan keyakinan {gill_result['confidence']*100:.1f}%.
• Kedua organ ini dianalisis secara terpisah sebelum digabungkan.

**Kesimpulan Akhir**
• Status akhir ikan adalah {final_label.lower()}.
• Keyakinan sistem sebesar {confidence_percent:.1f}%.

**Rekomendasi Penanganan**
• Gunakan hasil sebagai informasi pendukung.
• Simpan ikan di suhu dingin.
• Tetap lakukan pemeriksaan kondisi fisik ikan.
""".strip()


    # =====================================================
    # RESPONSE
    # =====================================================

    return {

        # -----------------------------
        # Eye
        # -----------------------------

        "eye": {

            "label": (
                eye_result["label"]
            ),

            "confidence": round(
                eye_result[
                    "confidence"
                ],
                4,
            ),

            "prob_fresh": round(
                eye_result[
                    "prob_fresh"
                ],
                4,
            ),

            "prob_nonfresh": round(
                eye_result[
                    "prob_nonfresh"
                ],
                4,
            ),

            "decision_method": (
                "single_best_model"
            ),

            "model": (
                eye_result[
                    "filename"
                ]
            ),
        },


        # -----------------------------
        # Gill
        # -----------------------------

        "gill": {

            "label": (
                gill_result["label"]
            ),

            "confidence": round(
                gill_result[
                    "confidence"
                ],
                4,
            ),

            "prob_fresh": round(
                gill_result[
                    "prob_fresh"
                ],
                4,
            ),

            "prob_nonfresh": round(
                gill_result[
                    "prob_nonfresh"
                ],
                4,
            ),

            "decision_method": (
                "single_best_model"
            ),

            "model": (
                gill_result[
                    "filename"
                ]
            ),
        },


        # -----------------------------
        # Final fusion
        # -----------------------------

        "final": {

            "label": (
                final_label
            ),

            "confidence": round(
                final_confidence,
                4,
            ),

            "prob_fresh": round(
                final_prob_fresh,
                4,
            ),

            "prob_nonfresh": round(
                final_prob_nonfresh,
                4,
            ),

            "decision_reason": (
                prediction[
                    "final"
                ][
                    "decision_reason"
                ]
            ),

            "is_disagreement": (
                prediction[
                    "final"
                ][
                    "is_disagreement"
                ]
            ),

            "note": (
                prediction[
                    "final"
                ][
                    "note"
                ]
            ),
        },


        # -----------------------------
        # Fusion information
        # -----------------------------

        "fusion": {

            "method": (
                "conservative_decision_level_"
                "late_fusion"
            ),

            "nonfresh_veto_confidence": (
                NONFRESH_VETO_CONFIDENCE
            ),
        },


        # =================================================
        # COMPATIBILITY DENGAN FRONTEND LAMA
        # =================================================

        "ensemble_method": (
            "conservative_decision_level_"
            "late_fusion"
        ),

        "fusion_method": (
            "conservative_decision_level_"
            "late_fusion"
        ),

        "label": (
            final_label
        ),

        "confidence": round(
            final_confidence,
            4,
        ),

        "confidence_percent": round(
            confidence_percent,
            2,
        ),

        "confidence_level": (
            confidence_level
        ),

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

        "explanation": (
            explanation
        ),
    }
