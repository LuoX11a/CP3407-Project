---
layout: default
title: Class Diagram
parent: Documentation
---

# ParkGuideSG — Class Diagram

```mermaid
classDiagram
    direction TB

    class Carpark {
        +String carpark_id PK
        +String address
        +Int car_lots
        +Int motorcycle_lots
        +Float lat
        +Float lng
        +Float svy21_x
        +Float svy21_y
    }

    class AvailabilityLog {
        +BigInt id PK
        +String carpark_id FK
        +Timestamp timestamp
        +Int available_lots
        +Float vacancy_rate
        +String weather_condition
        +Int hour
        +Int day_of_week
        +Bool is_weekend
        +Bool is_public_holiday
    }

    class WeatherStation {
        +String station_id PK
        +String name
        +Float lat
        +Float lng
    }

    class WeatherRecord {
        +BigInt id PK
        +String station_id FK
        +Timestamp timestamp
        +Float temperature
        +Float humidity
        +Float rainfall
        +String weather_condition
    }

    class User {
        +Int id PK
        +String username
        +String email
        +String password_hash
        +Timestamp created_at
    }

    class Favourite {
        +Int id PK
        +Int user_id FK
        +String carpark_id FK
        +Timestamp created_at
    }

    class MLPrediction {
        +BigInt id PK
        +String carpark_id FK
        +Timestamp prediction_time
        +Timestamp forecast_timestamp
        +Float predicted_vacancy_rate
        +Int predicted_available_lots
        +String model_version
        +Float[] trend_series
    }

    class MLModel {
        +String model_version PK
        +String model_type
        +Timestamp training_start
        +Timestamp training_end
        +JSONB metrics
    }

    class PublicHoliday {
        +Date date PK
        +String name
    }

    Carpark "1" --> "*" AvailabilityLog : has
    Carpark "1" --> "*" MLPrediction : forecasted by
    Carpark "1" --> "*" Favourite : favourited by
    WeatherStation "1" --> "*" WeatherRecord : records
    User "1" --> "*" Favourite : saves
    MLModel "1" --> "*" MLPrediction : generates
```

## Entity Descriptions

| Entity | Purpose | Source |
|--------|---------|--------|
| **Carpark** | Static HDB carpark metadata (address, capacity, coordinates) | `04_bootstrap_carparks.py` from data.gov.sg |
| **AvailabilityLog** | Time-series parking availability, enriched with temporal features | `etl_cloud.py` every 30 min |
| **WeatherStation** | NEA weather station locations (47 stations) | NEA 2-hour forecast API |
| **WeatherRecord** | Timestamped weather readings per station | NEA measurement APIs |
| **User** | Registered user accounts (JWT auth, bcrypt passwords) | `/auth/register` endpoint |
| **Favourite** | User-to-carpark bookmark relationship | `/favourites` CRUD |
| **MLPrediction** | Cached vacancy predictions for the live map | `ml/train.py` + `ml/predict.py` |
| **MLModel** | Deployed model versions and training metadata | Training pipeline |
| **PublicHoliday** | Singapore public holidays for temporal features | `02_seed_holidays.sql` |

## Key Relationships

- `AvailabilityLog` → `Carpark`: Foreign key with cascade; main query path for time-series
- `MLPrediction` → `Carpark`: Cached forecasts updated after each training run
- `Favourite` → `User` + `Carpark`: Enables per-user bookmark management
- `WeatherRecord` → `WeatherStation`: Links measurements to station metadata
