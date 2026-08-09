from config import NONFRESH_VETO_CONFIDENCE
from utils.math_utils import normalize_probability

def fuse_predictions(
    eye_result: dict,
    gill_result: dict,
) -> dict:

    """
    Conservative Decision-Level Late Fusion.

    Aturan:
    1. Jika mata dan insang sepakat:
       - Fresh + Fresh       -> Fresh
       - NonFresh + NonFresh -> NonFresh

    2. Jika mata dan insang berbeda:
       - Jika organ yang memprediksi NonFresh memiliki
         confidence >= NONFRESH_VETO_CONFIDENCE,
         hasil akhir = NonFresh.

       - Jika confidence NonFresh belum cukup kuat,
         hasil akhir = Perlu Pemeriksaan Lanjutan.

    Tujuan:
    Mencegah rata-rata probabilitas 50:50 menghasilkan
    keputusan Fresh pada kondisi konflik ekstrem.
    """

    eye_class = eye_result[
        "class_index"
    ]

    gill_class = gill_result[
        "class_index"
    ]

    eye_prob_nonfresh = eye_result[
        "prob_nonfresh"
    ]

    gill_prob_nonfresh = gill_result[
        "prob_nonfresh"
    ]

    # =====================================================
    # KONDISI 1
    # KEDUA ORGAN SEPAKAT
    # =====================================================

    if eye_class == gill_class:

        # ---------------------------------
        # Keduanya NonFresh
        # ---------------------------------

        if eye_class == 1:

            final_class = 1
            final_label = "TIDAK SEGAR"

            # Rata-rata digunakan untuk SCORE,
            # bukan untuk menentukan kelas.
            final_prob_nonfresh = (
                eye_prob_nonfresh
                + gill_prob_nonfresh
            ) / 2

            final_confidence = (
                eye_result["confidence"]
                + gill_result["confidence"]
            ) / 2

            decision_reason = (
                "both_organs_nonfresh"
            )

            is_disagreement = False

        # ---------------------------------
        # Keduanya Fresh
        # ---------------------------------

        else:

            final_class = 0
            final_label = "SEGAR"

            final_prob_nonfresh = (
                eye_prob_nonfresh
                + gill_prob_nonfresh
            ) / 2

            final_confidence = (
                eye_result["confidence"]
                + gill_result["confidence"]
            ) / 2

            decision_reason = (
                "both_organs_fresh"
            )

            is_disagreement = False

    # =====================================================
    # KONDISI 2
    # ORGAN TIDAK SEPAKAT
    # =====================================================

    else:

        is_disagreement = True

        if eye_class == 1:

            nonfresh_result = eye_result
            fresh_result = gill_result

            nonfresh_organ = "eyes"
            fresh_organ = "gills"

        else:

            nonfresh_result = gill_result
            fresh_result = eye_result

            nonfresh_organ = "gills"
            fresh_organ = "eyes"

        nonfresh_confidence = (
            nonfresh_result[
                "confidence"
            ]
        )

        # =================================================
        # STRONG NONFRESH VETO
        # =================================================

        if (
            nonfresh_confidence
            >= NONFRESH_VETO_CONFIDENCE
        ):

            final_class = 1

            final_label = (
                "TIDAK SEGAR"
            )

            final_confidence = (
                nonfresh_confidence
            )

            final_prob_nonfresh = (
                nonfresh_result[
                    "prob_nonfresh"
                ]
            )

            decision_reason = (
                "strong_nonfresh_veto"
            )

        # =================================================
        # DISAGREEMENT TIDAK CUKUP KUAT
        # =================================================

        else:

            final_class = None

            final_label = (
                "PERLU PEMERIKSAAN "
                "LANJUTAN"
            )

            final_prob_nonfresh = (
                eye_prob_nonfresh
                + gill_prob_nonfresh
            ) / 2

            final_confidence = 0.5

            decision_reason = (
                "organ_disagreement"
            )

    final_prob_nonfresh = (
        normalize_probability(
            final_prob_nonfresh
        )
    )

    final_prob_fresh = (
        normalize_probability(
            1.0
            - final_prob_nonfresh
        )
    )

    # =====================================================
    # CATATAN UNTUK FRONTEND
    # =====================================================

    if (
        decision_reason
        == "both_organs_fresh"
    ):

        note = (
            "Model mata dan insang "
            "konsisten menunjukkan "
            "kondisi segar."
        )

    elif (
        decision_reason
        == "both_organs_nonfresh"
    ):

        note = (
            "Model mata dan insang "
            "konsisten menunjukkan "
            "kondisi tidak segar."
        )

    elif (
        decision_reason
        == "strong_nonfresh_veto"
    ):

        note = (
            "Hasil mata dan insang berbeda. "
            "Salah satu organ menunjukkan "
            "indikasi tidak segar dengan "
            "keyakinan tinggi sehingga "
            "sistem menggunakan keputusan "
            "konservatif."
        )

    else:

        note = (
            "Hasil mata dan insang "
            "belum selaras dan indikasi "
            "tidak segar belum cukup kuat. "
            "Disarankan pemeriksaan fisik."
        )

    return {

        "eye": eye_result,

        "gill": gill_result,

        "final": {

            "class_index": (
                final_class
            ),

            "label": (
                final_label
            ),

            "confidence": (
                normalize_probability(
                    final_confidence
                )
            ),

            "decision_reason": (
                decision_reason
            ),

            "is_disagreement": (
                is_disagreement
            ),

            "note": note,
        },

        "final_prob_nonfresh": (
            final_prob_nonfresh
        ),

        "final_prob_fresh": (
            final_prob_fresh
        ),

        "fusion": {

            "method": (
                "conservative_"
                "decision_level_"
                "late_fusion"
            ),

            "nonfresh_veto_confidence": (
                NONFRESH_VETO_CONFIDENCE
            ),
        },
    }
