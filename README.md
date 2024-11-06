# Run Analysis Streamlit App
**Version: 1.3**

## Description
The Run Analysis App is designed to track your running schedule and set personalized performance goals for the following week. Built on a schedule recommended by the Naval Special Warfare Department (NSW) and validated against peer-reviewed research, this app enables comprehensive tracking of running metrics—such as endurance, stamina, and speed—through individualized weekly goals. Integration with Snowflake provides secure data storage, multi-user authentication, and tailored insights into each user’s progress and potential.

## Suggested Companion App
For optimal use, we recommend gathering run data from a health and GPS monitoring app like the Nike Run Club Mobile App. This app provides detailed metrics such as distance, pace, and cadence, which can be logged into the Run Analysis App for goal setting and performance analysis.

## Project Structure
### 1. Database Setup
**Database:** `run_analysis_db`  
**Schema:** `run_data_schema`  
**Tables:**
- **users:** Stores user information for authentication and account management.
- **run_data:** Logs each run’s details, including type, distance, cadence, effort, and environmental factors.
- **user_schedule_progress:** Tracks weekly progress for users in each run type category (endurance, stamina, speed).

### 2. Tables and Fields
#### Users Table: `users`
| Field          | Type    | Description                              |
|----------------|---------|------------------------------------------|
| user_id        | INT     | Primary Key, unique user identifier      |
| username       | VARCHAR | Unique username for user login           |
| email          | VARCHAR | User's email, used for login and recovery|
| password_hash  | VARCHAR | Hashed password                          |

#### Run Data Table: `run_data`
Logs detailed information for each run entry, supporting both high-level insights and granular analysis.

| Column             | Data Type             | Description                                                       |
|--------------------|-----------------------|-------------------------------------------------------------------|
| `RUN_ID`           | NUMBER(38,0)          | Primary key, unique identifier for each run                       |
| `USER_ID`          | NUMBER(38,0)          | Foreign key linking to the `users` table                          |
| `RUN_TYPE`         | VARCHAR(16777216)     | Type of run: 'Endurance', 'Stamina', or 'Speed'                   |
| `DISTANCE`         | FLOAT                 | Total distance covered during the run (miles)                     |
| `AVG_PACE`         | VARCHAR(16777216)     | Average pace for the run, displayed as minutes per mile/km        |
| `CADENCE`          | NUMBER(38,0)          | Average steps per minute                                          |
| `EFFORT`           | FLOAT                 | Self-rated effort level on a 1.0 to 10.0 scale                    |
| `LOCATION`         | VARCHAR(16777216)     | Location of the run (e.g., Street, Track, Trail)                  |
| `MUSIC_BPM`        | NUMBER(38,0)          | Music beats per minute during the run                             |
| `BREATHING_TEMPO`  | VARCHAR(16777216)     | Breathing pattern in steps per inhale/exhale                      |
| `RUN_DATE`         | TIMESTAMP_NTZ(9)      | Timestamp of the run, defaults to current date and time           |
| `RUN_TIME`         | NUMBER(38,0)          | Total duration of the run in seconds                              |
| `RUN_TIME_SECONDS` | NUMBER(38,0)          | Alternative representation of run duration in seconds             |
| `REPS`             | NUMBER(38,0)          | Number of repetitions (intervals) for specific run types          |
| `REP_DISTANCE`     | FLOAT                 | Distance per repetition for interval training (miles)             |
| `REP_TIME`         | FLOAT                 | Time per repetition for interval training (seconds)               |

#### User Schedule Progress Table: `user_schedule_progress`
| Field            | Type      | Description                                 |
|------------------|-----------|---------------------------------------------|
| user_id          | INT       | Foreign Key, links to `users.user_id`       |
| endurance_week   | FLOAT     | Average weekly endurance metrics            |
| stamina_week     | FLOAT     | Average weekly stamina metrics              |
| speed_week       | FLOAT     | Average weekly speed metrics                |

## Key Functionalities
### User Authentication
- Register, login, and password recovery functionality with secure password hashing.
  
### Run Data Logging
- Allows users to log detailed run information, including metrics and environmental factors like location and music BPM.

### Weekly Goal Tracking
- Tracks user progress across endurance, stamina, and speed categories, adjusting weekly goals based on data inputs. Default goals are generated for new users from `schedule_df`.

### Scorecard Display
- Introduces color-coded scorecards for each run type (endurance, stamina, speed) that display target goals alongside user performance. Supports mobile and desktop views.

### Data Visualization
- Summarizes and visualizes key metrics in the app interface. Displays top-level metrics (distance, pace, music BPM) prominently, with additional details accessible for each run type.

### Real-time Progress Tracking
- Tracks user progress toward weekly goals in endurance, stamina, and speed, dynamically adjusting schedules based on user performance.

### Mobile-Optimized UI
- Mobile-first interface featuring stacked scorecards for easy navigation, a bottom navigation bar, and toggle options for weekly, monthly, and yearly views of metrics.

### Enhanced Error Handling
- Added handling for cases where user data is absent. Defaults to a beginner-friendly goal structure if no prior data is available, ensuring a seamless experience for new users.

### Manual Goal Adjustments
- Users can manually adjust performance goals, with an option to reset to app-generated defaults.

## Predefined Queries
```sql
-- Retrieve all data for a specific user
SELECT * FROM run_data WHERE user_id = [user_id];

-- Weekly average pace for a specific user
SELECT AVG(run_time/distance) AS avg_pace FROM run_data 
WHERE user_id = [user_id] AND run_type = 'Endurance';

-- All runs grouped by type for user
SELECT run_type, COUNT(run_id), AVG(distance), AVG(cadence), AVG(effort) 
FROM run_data WHERE user_id = [user_id] GROUP BY run_type;
```

## Usage Notes

- **Data Aggregation:** Uses timestamps and grouping by `run_type` for detailed analytics on user performance.
- **Security:** Each user’s data is isolated; queries should include `user_id` for user-specific retrieval.
- **Data Security:** Implements Snowflake’s role-based access controls to restrict access to sensitive information, ensuring each user can only access their own data.
- **Sensitive Information:** Handles sensitive user data (like email addresses and hashed passwords) through secure Snowflake storage, accessible only through authenticated API calls.
- **Effort Tracking:** Recorded on a 1-10 scale with 0.5 increments to track intensity.
