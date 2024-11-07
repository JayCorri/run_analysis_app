# Run Analysis Streamlit App
**Version: 2.0**

## Description
The Run Analysis App provides personalized run training analytics with flexible weekly goals and performance metrics. Now featuring a choice between the "NSW Candidate Run Regimen" and the "Marathon Trainer Regimen," the app enables users to follow structured training schedules, dynamically adjusting based on performance and progression.

## Suggested Companion App
For data logging, use a GPS-enabled running app like Nike Run Club. Gather metrics like distance, pace, and cadence, which can then be logged in the Run Analysis App for customized goal setting and progress tracking.

## Key Functionalities

### User Authentication
- **Register/Login**: Secure account creation and access, with password encryption for secure storage.
  
### Training Regimen Selection
- **Dynamic Regimen Switching**: Users can choose from stored regimens, with "NSW Candidate Run Regimen" as the default for new users.
- **Regimen-Specific Goals**: Tracks endurance, stamina, and speed for each regimen, adjusting goals dynamically.

### Run Data Logging
- **Flexible Data Entry**: Users can log detailed metrics, including run type, distance, time, cadence, effort, location, and breathing patterns.
  
### Weekly Goal Tracking
- **Regimen-Based Goals**: Weekly targets are generated from the chosen regimen, supporting each user’s unique pace and progression.
- **Scorecards**: Each run type (endurance, stamina, speed) has a color-coded scorecard showing target goals and user performance.

### Data Visualization
- **Performance Analysis**: Visualize weekly distance, pace, and stamina metrics with charts for each run type.
- **Goal Progress Tracking**: Progress toward weekly goals is dynamically displayed, encouraging consistent improvement.

### Maintenance Mode
- **Automatic Transition**: When a user completes all weeks in a regimen, they are prompted to enter "Maintenance Mode" or switch to a new regimen, such as the "Marathon Trainer Regimen."

### Mobile-Optimized UI
- **Responsive Design**: Mobile-first layout with bottom navigation for quick access to main features, including performance goals, metrics, and data entry.

### Error Handling
- **Regimen Transitions**: Smooth user experience when switching regimens or completing the final week in a schedule.
- **Enhanced Validation**: Ensures data integrity, especially when users update schedules or switch regimens.

## Database and Project Structure

### Database Setup
**Database:** `run_analysis_db`  
**Schema:** `run_data_schema`  
**Tables:**
- **users:** Authentication and account management.
- **run_data:** Detailed records for each logged run.
- **training_regimens:** Stores training schedules for each available regimen.
- **user_schedule_progress:** Tracks weekly progress across endurance, stamina, and speed metrics.

#### Training Regimens Table: `training_regimens`
Stores weekly training data for each available regimen, supporting easy switching and expansion.

| Column              | Type    | Description                                           |
|---------------------|---------|-------------------------------------------------------|
| `regimen_name`      | VARCHAR | Name of the regimen (e.g., NSW Candidate Run Regimen) |
| `week_number`       | INT     | Week number in the regimen                            |
| `endurance_goal`    | FLOAT   | Target distance for endurance runs                    |
| `stamina_reps`      | INT     | Repetitions for stamina training                      |
| `stamina_time_per_rep` | INT  | Time per stamina rep in minutes                       |
| `speed_reps`        | INT     | Repetitions for speed intervals                       |
| `speed_distance_per_rep` | FLOAT | Distance per speed rep (miles)                     |

## Example Queries

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
---

## Usage Notes

- **Data Aggregation**: Aggregates weekly performance data by `run_type` (endurance, stamina, speed) to provide personalized insights and goal setting.
- **Secure User Data**: Implements Snowflake's role-based access to keep user data secure. Sensitive data like email addresses and passwords are encrypted and stored securely.
- **Error Handling**: Extensive error handling ensures the app gracefully manages scenarios such as missing user data, regimen transitions, and empty schedules.
- **User-Friendly Progress Tracking**: Weekly goals are automatically set based on the user’s selected regimen and adjusted dynamically each week.
- **Maintenance Mode**: Allows users who complete all weeks in a regimen to either stay in a maintenance schedule or transition to a more advanced regimen, with suggestions based on their current performance level.

## Future Enhancements

- **Additional Regimens**: Expand the regimen library to include options tailored for specific goals, such as trail running, ultra-marathons, or recreational 5K training.
- **Advanced Analytics**: Incorporate deeper insights, such as tracking trends over time, visualizing improvements in pace, or measuring heart rate data.
- **Personalized Recommendations**: Provide automated recommendations for users based on performance history and feedback, suggesting regimen adjustments or cross-training.

**Version: 2.1**

### Training Regimens and Schedules

To accommodate multiple training regimens, the database includes:

- **TRAINING_REGIMENS Table**: Stores available regimens, each identified by a unique `regimen_id` and `regimen_name`.
- **SCHEDULES Table**: Stores weekly schedule details for each regimen, referenced by `regimen_id` to link to the respective regimen in `TRAINING_REGIMENS`.

This structure supports future flexibility, allowing new regimens to be added easily without altering the app’s core functionality.

#### TRAINING_REGIMENS Table
| Column         | Data Type | Description                       |
|----------------|-----------|-----------------------------------|
| `regimen_id`   | INT       | Unique identifier for each regimen |
| `regimen_name` | VARCHAR   | Descriptive name of the regimen   |

#### SCHEDULES Table
| Column                   | Data Type | Description                                          |
|--------------------------|-----------|------------------------------------------------------|
| `schedule_id`            | INT       | Unique identifier for each schedule entry            |
| `regimen_id`             | INT       | Foreign key linking to `TRAINING_REGIMENS`           |
| `week`                   | INT       | Week number within the regimen                       |
| `endurance_distance`     | FLOAT     | Distance goal for endurance runs                     |
| `stamina_reps`           | INT       | Number of reps for stamina training                  |
| `stamina_time_per_rep`   | FLOAT     | Time allocated per stamina rep                       |
| `speed_reps`             | INT       | Number of speed repetitions                          |
| `speed_distance_per_rep` | FLOAT     | Distance per speed repetition                        |

Each entry in `SCHEDULES` corresponds to a specific week and regimen, facilitating easy filtering and display of schedules in the app.


## New Features in v3.0

### Session Persistence
User-selected regimen and weekly training goals are now persistent across sessions, allowing users to resume where they left off upon logging back in. This change provides a seamless experience with personalized progression tracking.

### Custom Regimen Logic
The app includes special week handling per regimen:
- **NSW Candidate Regimen**: If the user completes the 34-week training program and does not choose to begin the Marathon regimen, the app automatically places the user in maintenance mode, repeating week 34 goals.
- **Marathon Trainer Regimen**: Recognizes specific training weeks:
  - **Marathon Week** (first week of the month)
  - **Short and Fast Week** (last week of the month)
  - **Normal Week** (all other weeks)

These features ensure a tailored experience based on the user’s selected regimen and training progress.

### Database Consolidation
All schedule data is now consolidated within a Snowflake table (`schedules`), enabling a unified structure for accessing and updating user goals.

---

## Setup Requirements

Ensure the following configurations for deploying the app:
1. **Snowflake Database Configuration**:
   - The `users` and `schedules` tables should be configured in Snowflake as per v3.0 schema changes.
   - User credentials and session data are managed within Snowflake.

2. **Dependencies**:
   - Required packages in `requirements.txt` include:
     - `streamlit`
     - `snowflake-connector-python`
     - `snowflake-sqlalchemy`
     - `bcrypt`
     - `pandas`
     - `matplotlib`
     - `sqlalchemy`

Refer to the **CHANGELOG.md** for a full list of enhancements and changes in this release.
