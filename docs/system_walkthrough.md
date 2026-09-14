# Sensor Track System — End-to-End Walkthrough

## 1. Synthetic Sensor Report

The simulator generates a sensor observation containing:

- sensor ID
- source track ID
- latitude
- longitude
- altitude
- heading
- speed
- timestamp

The simulator submits the observation to:

POST /observations


## 2. Observation Validation

FastAPI receives the observation through the SensorObservation schema.

The schema validates:

- latitude range
- longitude range
- heading range
- non-negative speed
- timezone-aware timestamp


## 3. Track Association

The backend attempts to determine whether the observation belongs to an existing system track.

### Source continuity

The system first checks whether the same:

sensor_id + source_track_id

has contributed to a system track recently.

Source continuity expires after the configured continuity window so that reused sensor track IDs are not trusted indefinitely.

### Correlation

If recent source continuity is unavailable, candidate system tracks are evaluated using:

- observation timing
- predicted track position
- geographic distance
- altitude difference
- speed difference
- heading difference

Candidates outside configured gates are rejected.

Remaining candidates receive an association score.

Lower scores represent better matches.

If no candidate qualifies, a new system-owned track ID is created.


## 4. System Track Identity

Sensor identities and system identities are intentionally separate.

Example:

RADAR-01 / RDR-441
EO-02 / EO-827

may both contribute to:

SYS-A1B2C3D4E5F6

The SYS identity is authoritative inside the application.


## 5. Track Quality

Each system track maintains a quality value from:

0.0 to 1.0

New tracks begin at:

0.50

Quality changes as additional evidence arrives.

Source continuity and strong correlations increase quality.

Weak correlations can decrease quality.


## 6. State Estimation

For an existing track, incoming measurements do not directly overwrite the complete system state.

The estimator blends the previous system state with the incoming measurement for:

- latitude
- longitude
- altitude
- speed
- heading

Heading uses circular-angle logic so transitions such as:

359° → 1°

are handled correctly.


## 7. Persistence

PostgreSQL stores:

### Tracks
The latest estimated state of each system track.

### Observations
The historical sensor reports associated with each system track.

### Track Sources
The sensor/source identities that have contributed to each system track, including:

- first seen
- last seen
- observation count


## 8. Track Status

Track freshness is calculated from its last-seen timestamp.

Tracks transition through:

ACTIVE
STALE
DROPPED

Track status is separate from track quality.

A track can therefore be high quality but currently dropped.


## 9. Real-Time Distribution

After the database transaction succeeds, FastAPI broadcasts the updated track state through WebSockets.

The REST API is also available for:

- current tracks
- individual tracks
- observation history
- contributing sources
- searches and filtering


## 10. React / TypeScript Dashboard

The frontend consumes REST data and WebSocket updates.

The operator interface provides:

- interactive map
- live track markers
- track selection
- search
- filtering
- ACTIVE / STALE / DROPPED status
- track quality
- sensor information
- position
- altitude
- speed
- heading
- historical charts
- track trails


## 11. Reliability and Testing

The system is containerized with Docker.

PostgreSQL schema changes are managed with Alembic.

The automated test suite covers areas including:

- API behavior
- association
- ambiguous targets
- motion prediction
- association confidence
- track quality
- source provenance
- source continuity expiration
- reacquisition
- state estimation
- circular heading handling
- database foreign-key behavior