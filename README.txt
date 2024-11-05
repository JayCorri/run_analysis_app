Run Analysis Streamlit App
Version: 1.2

Description  
The Run Analysis App is designed to track your run schedule and set personalized performance goals for the following week. The schedule embedded in the app is based on a routine recommended for candidates by the Naval Special Warfare Department (NSW), which the developer validated against peer-reviewed research for scientific soundness. This app enables comprehensive tracking of user running metrics—such as endurance, stamina, and speed—through individualized weekly goals. The integration with Snowflake provides secure data storage, multi-user authentication, and tailored insights into each user’s progress and potential.

Suggested Companion App  
For optimal use, we recommend gathering run data from a health and GPS monitoring app like the Nike Run Club Mobile App. This app provides detailed metrics, such as distance, pace, and cadence, which can be logged into the Run Analysis App for comprehensive tracking, performance goal setting, and analysis.

Project Structure
1. Database Setup
Database: run_analysis_db
Schema: run_data_schema
Tables:
users: Stores user information for authentication and account management.
run_data: Logs each run’s details, including type, distance, cadence, effort, and environmental factors.
2. Tables and Fields
Users Table: users
Field	Type	Description
user_id	INT	Primary Key, unique user identifier
username	VARCHAR	Unique username for user login
email	VARCHAR	User's email, used for login and recovery
password_hash	VARCHAR	Hashed password
Run Data Table: run_data
Field	Type	Description
run_id	INT	Primary Key, unique identifier for each run
user_id	INT	Foreign Key, links to users.user_id
run_type	VARCHAR	Type of run: 'Endurance', 'Stamina', or 'Speed'
distance	FLOAT	Distance covered (miles)
avg_pace	VARCHAR	Average pace ('minutes
')
run_time	NUMBER	Duration (seconds)
cadence	NUMBER	Steps per minute
effort	FLOAT	Perceived effort on scale of 1.0 to 10.0
location	VARCHAR	Location of run (Street, Track, or Trail)
music_bpm	NUMBER	Music beats per minute
breathing_tempo	VARCHAR	Breathing ratio (e.g., '2:2' for inhale/exhale steps)
run_date	TIMESTAMP	Auto-updated timestamp of the run

Key Functionalities
User Authentication:
Register, login, and password recovery functionality with secure password hashing.

Run Data Logging:
Allows users to log details of their runs, including metrics and environmental factors like location and music bpm.

Weekly Goal Tracking:
Tracks user progress in endurance, stamina, and speed, adjusting weekly goals based on input data.

Data Visualization:
Summarizes and visualizes key metrics in the Streamlit app interface.

Real-time Progress Tracking:
Tracks user progress toward weekly endurance, stamina, and speed goals, adjusting schedules incrementally based on user performance.

Predefined Queries
sql
-- Sample queries for testing and retrieving data --

-- Retrieve all data for a specific user
SELECT * FROM run_data WHERE user_id = [user_id];

-- Weekly average pace for a specific user
SELECT AVG(run_time/distance) AS avg_pace FROM run_data 
WHERE user_id = [user_id] AND run_type = 'Endurance';

-- All runs grouped by type for user
SELECT run_type, COUNT(run_id), AVG(distance), AVG(cadence), AVG(effort) 
FROM run_data WHERE user_id = [user_id] GROUP BY run_type;

Usage Notes
Data Aggregation:
Use timestamps and grouping by run_type for detailed analytics on user performance.

Security:
Each user’s data is isolated; queries should include user_id for user-specific retrieval.

Data Security:
Implements Snowflake’s role-based access controls to restrict access to sensitive information, ensuring each user can only access their own data.

Sensitive Information:
Handles sensitive user data (like email addresses and hashed passwords) through secure Snowflake storage, accessible only through authenticated API calls.

Effort Tracking:
Recorded on a 1-10 scale with 0.5 increments to track intensity.
