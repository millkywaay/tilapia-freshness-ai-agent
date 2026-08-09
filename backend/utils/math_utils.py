import math
import numpy as np

def normalize_probability(
    value: float,
) -> float:

    value = float(value)

    if not math.isfinite(
        value
    ):
        raise ValueError(
            "Probabilitas non-finite."
        )

    if (
        value < -1e-5
        or value > 1.00001
    ):
        raise ValueError(
            "Output model di luar "
            f"rentang 0-1: {value}"
        )

    return min(
        max(
            value,
            0.0,
        ),
        1.0,
    )


def extract_nonfresh_probability(
    raw_prediction,
) -> float:
    if isinstance(
        raw_prediction,
        dict,
    ):
        raw_prediction = next(
            iter(
                raw_prediction.values()
            )
        )

    if isinstance(
        raw_prediction,
        (list, tuple),
    ):

        if not raw_prediction:
            raise ValueError(
                "Model tidak menghasilkan output."
            )

        raw_prediction = (
            raw_prediction[0]
        )

    prediction_array = np.asarray(
        raw_prediction,
        dtype=np.float64,
    ).reshape(-1)

    if prediction_array.size == 1:

        probability = (
            prediction_array[0]
        )

    elif prediction_array.size == 2:

        probability = (
            prediction_array[1]
        )

    else:

        raise ValueError(
            "Output model harus berupa "
            "sigmoid 1 output atau "
            "softmax 2 output."
        )

    return normalize_probability(
        probability
    )
