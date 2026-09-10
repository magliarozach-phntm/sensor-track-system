import math
import os
import random
import time
from datetime import datetime, timezone

import requests
from dotenv import load_dotenv

load_dotenv()

API_BASE_URL = os.getenv(
    "SENSOR_API_URL",
    "http://127.0.0.1:8000"
)

OBSERVATION_URL = (
    f"{API_BASE_URL}/observations"
)

outages = {}

next_track_id = 1004

tracks = {
    "TRK-1001": {
        "sensor_id": "RADAR-01",
        "latitude": 34.9200,
        "longitude": -80.9100,
        "altitude": 12000,
        "heading": 90,
        "speed": 180,
    },
    "TRK-1002": {
        "sensor_id": "EO-02",
        "latitude": 34.9400,
        "longitude": -80.9500,
        "altitude": 8000,
        "heading": 210,
        "speed": 130,
    },
    "TRK-1003": {
        "sensor_id": "RADAR-03",
        "latitude": 34.9000,
        "longitude": -80.9300,
        "altitude": 16000,
        "heading": 330,
        "speed": 220,
    },
}

def update_track(track, seconds=2):
    # Small realistic variations
    track["heading"] = (
        track["heading"] + random.uniform(-2, 2)
    ) % 360

    track["speed"] = max(
        0,
        track["speed"] + random.uniform(-2, 2)
    )

    track["altitude"] += random.uniform(-50, 50)

    # Knots -> meters per second
    speed_mps = track["speed"] * 0.514444

    # Distance traveled during this update
    distance_m = speed_mps * seconds

    heading_rad = math.radians(track["heading"])

    # Resolve movement into north/east components
    north_m = distance_m * math.cos(heading_rad)
    east_m = distance_m * math.sin(heading_rad)

    # Approximate meters per degree latitude
    meters_per_degree_lat = 111_320

    latitude_rad = math.radians(track["latitude"])

    meters_per_degree_lon = (
        111_320 * math.cos(latitude_rad)
    )

    track["latitude"] += (
        north_m / meters_per_degree_lat
    )

    track["longitude"] += (
        east_m / meters_per_degree_lon
    )
    
    

    return track

def create_observation(track_id, track):
    return {
        'sensor_id': track['sensor_id'],
        'track_id': track_id,
        'latitude': track['latitude'],
        'longitude': track['longitude'],
        'altitude': track['altitude'],
        'heading': track['heading'],
        'speed': track['speed'],
        'timestamp': datetime.now(timezone.utc).isoformat(),
    }
    
def spawn_track():
    global next_track_id
    
    track_id = f"TRK-{next_track_id}"
    
    tracks[track_id] = {
        "sensor_id": random.choice([
            "RADAR-01",
            "EO-02",
            "RADAR-03"
        ]),
    "latitude": random.uniform(34.88, 34.96),
    "longitude": random.uniform(-80.97, -80.89),
    "altitude": random.uniform(5000, 20000),
    "heading": random.uniform(0, 360),
    "speed": random.uniform(100, 300)
    }
    
    next_track_id += 1
    
    print(f"{track_id} SPAWNED")    
    

def terminate_track(track_id):
    del tracks[track_id]
    
    if track_id in outages:
        del outages[track_id]
    
    print(f"{track_id} TERMINATED")
    
    
    
while True:

    if random.random() < 0.01:
        spawn_track()

    for track_id, track in list(tracks.items()):

        update_track(track)

        if len(tracks) > 3 and random.random() < 0.005:
            terminate_track(track_id)
            continue

        # Track currently in an outage
        if track_id in outages:
            if time.time() < outages[track_id]:
                print(f"{track_id} SENSOR OUTAGE")
                continue
            else:
                del outages[track_id]
                print(f"{track_id} REACQUIRED")

        # Small chance of starting a 12–20 second outage
        if random.random() < 0.02:
            outage_length = random.randint(12, 20)

            outages[track_id] = (
                time.time() + outage_length
            )

            print(
                f"{track_id} LOST - "
                f"{outage_length}s outage"
            )

            continue

        # Normal single-report dropout
        if random.random() < 0.05:
            print(
                f"{track_id} observation dropped"
            )
            continue

        observation = create_observation(
            track_id,
            track
        )

        response = requests.post(
            OBSERVATION_URL,
            json=observation,
            timeout=5
        )

        print(
            track_id,
            response.status_code,
            observation["latitude"],
            observation["longitude"]
        )

    time.sleep(2)



    