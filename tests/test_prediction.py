import pytest

from app.services.prediction import predict_position


def test_zero_seconds_returns_same_position():
    latitude = 34.92
    longitude = -80.93

    predicted_latitude, predicted_longitude = (
        predict_position(
            latitude=latitude,
            longitude=longitude,
            heading=90,
            speed=200,
            seconds=0,
        )
    )

    assert predicted_latitude == latitude
    assert predicted_longitude == longitude
    
def test_north_bound():
    latitude = 34.92
    longitude = -80.93
    
    predicted_latitude, predicted_longitude = (
        predict_position(
            latitude=latitude,
            longitude=longitude,
            heading = 0,
            speed = 200,
            seconds = 10
        )
    )
    
    assert predicted_latitude > latitude
    assert predicted_longitude == pytest.approx(longitude)
    
def test_south_bound():
    latitude = 34.92
    longitude = -80.93
    
    predicted_latitude, predicted_longitude = (
            predict_position(
                latitude=latitude,
                longitude=longitude,
                heading = 180,
                speed = 200,
                seconds = 10
            )
        )
        
    assert predicted_latitude < latitude
    assert predicted_longitude == pytest.approx(longitude)
    
def test_east_bound():
    latitude = 34.92
    longitude = -80.93
    
    predicted_latitude, predicted_longitude = (
            predict_position(
                latitude=latitude,
                longitude=longitude,
                heading = 90,
                speed = 200,
                seconds = 10
            )
        )
        
    assert predicted_latitude == pytest.approx(latitude)
    assert predicted_longitude > longitude
    
def test_west_bound():
    latitude = 34.92
    longitude = -80.93
    
    predicted_latitude, predicted_longitude = (
            predict_position(
                latitude=latitude,
                longitude=longitude,
                heading = 270,
                speed = 200,
                seconds = 10
            )
        )
        
    assert predicted_latitude == pytest.approx(latitude)
    assert predicted_longitude < longitude
    
def test_negative_seconds_rejected():
    with pytest.raises(
        ValueError,
        match="Prediction time cannot be negative"
    ):
        predict_position(
            latitude=34.92,
            longitude=-80.93,
            heading=90,
            speed=200,
            seconds=-5
        )
    
        