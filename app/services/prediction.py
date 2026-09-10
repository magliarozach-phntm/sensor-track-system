from math import cos, radians, sin


def predict_position(
    latitude: float,
    longitude: float,
    heading: float,
    speed: float,
    seconds: float,
) -> tuple[float, float]:

    if seconds < 0:
        raise ValueError(
        "Prediction time cannot be negative"
        )
    
    speed_mps = speed * 0.514444

    distance_m = speed_mps * seconds

    heading_radians = radians(heading)
    latitude_in_radians = radians(latitude)

    north_m = (
        distance_m
        * cos(heading_radians)
    )

    east_m = (
        distance_m
        * sin(heading_radians)
    )

    meters_per_degree_latitude = 111_320

    meters_per_degree_longitude = (
        111_320
        * cos(latitude_in_radians)
    )

    latitude_change = (
        north_m
        / meters_per_degree_latitude
    )

    longitude_change = (
        east_m
        / meters_per_degree_longitude
    )

    predicted_latitude = (
        latitude + latitude_change
    )

    predicted_longitude = (
        longitude + longitude_change
    )

    return (
        predicted_latitude,
        predicted_longitude
    )