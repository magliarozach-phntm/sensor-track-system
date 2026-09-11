from typing import Literal


AssociationMethod = Literal[
    "SOURCE_CONTINUITY",
    "CORRELATION",
]


def calculate_track_quality(
    current_quality: float,
    association_method: AssociationMethod,
    association_score: float | None,
) -> float:

    if not 0.0 <= current_quality <= 1.0:
        raise ValueError(
            "Current quality must be between 0.0 and 1.0"
        )

    new_quality = current_quality

    if association_method not in (
        "SOURCE_CONTINUITY",
        "CORRELATION",
    ):
        raise ValueError(
            "Invalid association method"
        )
    
    if association_method == "SOURCE_CONTINUITY":
        new_quality += 0.05

    elif association_method == "CORRELATION":

        if association_score is None:
            raise ValueError(
                "Correlation requires an association score"
            )

        if association_score <= 0.50:
            new_quality += 0.08

        elif association_score < 1.00:
            new_quality += 0.03

        else:
            new_quality -= 0.05

    new_quality = max(
        0.0,
        min(1.0, new_quality)
    )

    return new_quality