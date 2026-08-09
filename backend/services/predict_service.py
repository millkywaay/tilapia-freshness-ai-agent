import numpy as np
from config import CLASS_THRESHOLD
from utils.image_utils import preprocess_resnet
from utils.math_utils import extract_nonfresh_probability, normalize_probability

def predict_organ(
    loaded_model: dict,
    image_array: np.ndarray,
) -> dict:

    processed_image = preprocess_resnet(
        image_array
    )

    interpreter = loaded_model["model"]
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()
    
    interpreter.set_tensor(input_details[0]['index'], processed_image)
    interpreter.invoke()
    
    raw_prediction = interpreter.get_tensor(output_details[0]['index'])

    prob_nonfresh = (
        extract_nonfresh_probability(
            raw_prediction
        )
    )

    prob_fresh = 1.0 - prob_nonfresh

    if prob_nonfresh >= CLASS_THRESHOLD:
        class_index = 1
        label = "TIDAK SEGAR"
        confidence = prob_nonfresh

    else:
        class_index = 0
        label = "SEGAR"
        confidence = prob_fresh

    return {
        "organ": loaded_model["organ"],
        "filename": loaded_model["filename"],

        "class_index": class_index,
        "label": label,

        "confidence": normalize_probability(
            confidence
        ),

        "prob_fresh": normalize_probability(
            prob_fresh
        ),

        "prob_nonfresh": normalize_probability(
            prob_nonfresh
        ),

        "decision_method": "single_best_model",
    }
