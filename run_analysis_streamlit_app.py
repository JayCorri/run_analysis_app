"""
Run Analysis Streamlit App
Version: 1.3

Description:
This application tracks a user's run metrics and sets personalized weekly goals. Supports three run types (Endurance, Stamina, Speed) with unique metrics for each. 
Updated to include flexible fields for varying metrics (rep_count, rep_distance, rep_time) based on run type.
"""



from sqlalchemy import create_engine, text
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import bcrypt
import base64
import smtplib
from email.mime.text import MIMEText

# Initialize SQLAlchemy engine
def get_engine():
    return create_engine(
        f"snowflake://{st.secrets['SNOWFLAKE_USER']}:{st.secrets['SNOWFLAKE_PASSWORD']}@{st.secrets['SNOWFLAKE_ACCOUNT']}/{st.secrets['SNOWFLAKE_DATABASE']}/{st.secrets['SNOWFLAKE_SCHEMA']}?warehouse={st.secrets['SNOWFLAKE_WAREHOUSE']}&role={st.secrets['SNOWFLAKE_ROLE']}"
    )
        
# Register a new user with hashed password
def register_user(username, email, password):
    """
    Registers a new user by storing a username, email, and base64-encoded hashed password in the database.
    
    :param username: Unique identifier for the user.
    :param email: User's email address for login and recovery.
    :param password: Raw password which is hashed and base64-encoded before storing.
    :return: None
    Error Handling: Checks for duplicate entries and secure password hashing.
    Note: Password hash is base64-encoded for compatibility with Snowflake VARCHAR storage.
    """
    # Hash the password
    hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    # Convert binary hash to base64-encoded string for VARCHAR storage
    hashed_pw_str = base64.b64encode(hashed_pw).decode('utf-8')
    
    # Store in Snowflake as VARCHAR using SQLAlchemy engine
    engine = get_engine()
    with engine.connect() as conn:
        conn.execute(
            text("""
                INSERT INTO users (username, email, password_hash) 
                VALUES (:username, :email, :password_hash)
            """),
            {"username": username, "email": email, "password_hash": hashed_pw_str}
        )

# Authenticate user by verifying hashed password in database
def authenticate(username, password):
    """
    Authenticates a user by checking their base64-encoded hashed password in the database.
    
    :param username: Username for login.
    :param password: Plaintext password to verify against stored hash.
    :return: Boolean indicating whether authentication is successful.
    Error Handling: Handles cases of user not found and mismatched passwords.
    Note: Password hash is decoded from base64 back to binary before verification.
    """
    engine = get_engine()
    query = text("SELECT password_hash FROM users WHERE username = :username")
    
    with engine.connect() as conn:
        result = conn.execute(query, {"username": username}).fetchone()
        
        if result:
            # Decode the base64 stored hash back to binary
            stored_hash = base64.b64decode(result[0])
            return bcrypt.checkpw(password.encode('utf-8'), stored_hash)
    
    return False

# Function to send a password recovery email
def send_recovery_email(email, username, recovery_link):
    """
    Sends an email to the user with their username and a password reset link for recovery.

    :param email: The registered email address of the user.
    :param username: The user's username for personalization.
    :param recovery_link: The link for password recovery.
    """
    msg = MIMEText(f"Hello {username},\n\nClick here to reset your password: {recovery_link}")
    msg["Subject"] = "Password Recovery"
    msg["From"] = st.secrets["EMAIL"]["FROM_EMAIL"]
    msg["To"] = email
    with smtplib.SMTP(st.secrets["EMAIL"]["SMTP_SERVER"], st.secrets["EMAIL"]["SMTP_PORT"]) as server:
        server.login(st.secrets["EMAIL"]["USER"], st.secrets["EMAIL"]["PASSWORD"])
        server.sendmail(st.secrets["EMAIL"]["USER"], email, msg.as_string())

# Updated weekly running schedule table
schedule_data = {
    "Week": list(range(1, 35)),
    "Endurance Distance (miles)": [3, 3.25, 3.5, 3.75, 4, 4.25, 4.5, 4.75, 5, 5.25, 5.5, 5.75, 6, 6.25, 6.5, 6.75, 7, 7.25, 7.5, 7.75, 8, 8.25, 8.5, 8.75, 9, 9.25, 9.5, 9.75, 10, 10, 10, 10, 10, 10],
    "Stamina Reps": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 3, 3, 3, 3, 3, 3, 3, 3, 3],
    "Stamina Time per Rep (minutes)": [15, 15, 16, 16, 17, 17, 18, 18, 19, 19, 20, 12, 12, 14, 14, 14, 16, 16, 16, 18, 18, 18, 20, 20, 20, 14, 14, 14, 17, 17, 17, 20, 20, 20],
    "Speed Reps": [4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10],
    "Speed Distance per Rep (miles)": [0.25] * 34  # Each speed interval distance is 0.25 miles
}

# Convert to DataFrame
schedule_df = pd.DataFrame(schedule_data)

# Retrieves the user's schedule progress for endurance, stamina, and speed
def get_user_schedule_progress(username):
    """
    Retrieves the user's schedule progress for endurance, stamina, and speed.

    :param username: Unique identifier for the user.
    :return: Dictionary with progress data or default values if no data exists.
    Error Handling: Returns default values and displays an error message if 
                    database access fails.
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Query to check if user has any run data
            query = text("""
                SELECT AVG(distance) AS endurance_week,
                       AVG(cadence) AS stamina_week,
                       AVG(run_time) AS speed_week
                FROM run_data
                WHERE user_id = (SELECT user_id FROM users WHERE username = :username)
            """)
            result = conn.execute(query, {"username": username}).fetchone()
            
            # Return results if found; otherwise, default values
            if result and any(result):
                return {
                    "endurance_week": result[0] if result[0] is not None else 0,
                    "stamina_week": result[1] if result[1] is not None else 0,
                    "speed_week": result[2] if result[2] is not None else 0
                }
            else:
                return {
                    "endurance_week": 0,
                    "stamina_week": 0,
                    "speed_week": 0
                }
    except Exception as e:
        st.error("Error fetching user schedule progress. Please contact support.")
        return {
            "endurance_week": 0,
            "stamina_week": 0,
            "speed_week": 0
        }

# Function to update user's schedule week based on progress
def update_user_schedule_progress(username, category):
    """
    Increments the user's current week for a specific category if they have met the goal.

    :param username: Username of the user.
    :param category: Run category (endurance, stamina, or speed) to increment.
    :return: None
    Error Handling: Safely increments the specified category's week in the database.
    """
    engine = get_engine()
    valid_categories = ["endurance", "stamina", "speed"]
    
    # Ensure the category is valid to prevent SQL injection
    if category not in valid_categories:
        raise ValueError("Invalid category. Must be 'endurance', 'stamina', or 'speed'.")

    try:
        with engine.connect() as conn:
            query = text(f"""
                UPDATE user_schedule_progress
                SET {category}_week = {category}_week + 1
                WHERE username = :username
            """)
            conn.execute(query, {"username": username})
    except Exception as e:
        st.error("Error updating user schedule progress. Please contact support.")


# Function to check if user met weekly goals
def check_and_update_schedule(username, run_data):
    """
    Checks if the user met the scheduled goal for each run category and updates their schedule.
    :param username: Username of the user.
    :param run_data: Dictionary with user input for endurance, stamina, and speed data.
    :return: None
    """
    # Get current week goals
    user_weeks = get_user_schedule_progress(username)
    for run_type in ["endurance", "stamina", "speed"]:
        week = user_weeks[f"{run_type}_week"]
        scheduled_goal = schedule_df[schedule_df["Week"] == week].iloc[0][f"{run_type.capitalize()} Run"]
        
        # Check if user met or exceeded scheduled goal
        if run_data[run_type] >= scheduled_goal:
            update_user_schedule_progress(username, f"{run_type}_week")

# Get next week's goals based on training schedule
def get_next_week_goals(current_week):
    """
    Retrieves the distance, time, and interval goals for the upcoming week based on the training schedule.
    
    :param current_week: The user's current training week.
    :return: Dictionary with goals for endurance, stamina, and speed or None if no data is available.
    Error Handling: Returns None if next week’s data is unavailable.
    """
    next_week_data = schedule_df[schedule_df['Week'] == current_week + 1]
    if not next_week_data.empty:
        return {
            "Endurance Distance (miles)": next_week_data['Endurance Distance (miles)'].values[0],
            "Stamina Run (minutes)": next_week_data['Stamina Run (minutes)'].values[0],
            "Speed Intervals": next_week_data['Speed Intervals'].values[0]
        }
    return None

# This function displays the weekly running schedule goal and performance for the selected run type.
def display_run_goal_and_performance(run_type, weekly_schedule):
    """
    Displays the goal and performance metrics for the selected run type.
    
    :param run_type: Selected run type (Endurance, Stamina, Speed).
    :param weekly_schedule: Dictionary containing weekly goals and performance metrics.
    :return: None
    Error Handling: Displays default text if metrics are missing.
    """
    st.subheader(f"{run_type} Goal")
    
    # Display Goal Metrics
    goal_data = weekly_schedule.get(run_type, {}).get("goal", {})
    st.markdown("**Goal**")
    for metric, value in goal_data.items():
        st.write(f"{metric}: {value}")
    
    # Display Performance Metrics
    performance_data = weekly_schedule.get(run_type, {}).get("performance", {})
    st.markdown("**This Week's Performance**")
    for metric, value in performance_data.items():
        st.write(f"{metric}: {value}")

# This function displays the weekly running schedule section with a toggle for Endurance, Stamina, and Speed.
def weekly_schedule_view(weekly_schedule):
    """
    Displays the weekly running schedule with options to view goals and performance by run type.
    
    :param weekly_schedule: Dictionary containing goals and current performance data for each run type.
    :return: None
    Error Handling: Handles missing or incomplete data gracefully.
    """
    st.header("Weekly Running Schedule")
    
    # Toggle menu for selecting Endurance, Stamina, or Speed
    run_type = st.radio("Select Run Type", ("Endurance", "Stamina", "Speed"))
    
    # Display selected run type's goals and performance
    display_run_goal_and_performance(run_type, weekly_schedule)

# Retrieve user's weekly schedule progress from Snowflake or default to Week 1 beginner goals
def get_user_weekly_schedule(user_id, week_start_date):
    """
    Retrieves the user's weekly schedule progress for Endurance, Stamina, and Speed goals.
    If no data exists, defaults to "Week 1" goals from the pre-defined schedule.

    :param user_id: Unique identifier for the user.
    :param week_start_date: The start date of the week for the schedule.
    :return: Dictionary with weekly goals for endurance, stamina, and speed.
    Error Handling: Returns default values (Week 1 goals) from the schedule if no data is available.
    """
    engine = get_engine()
    
    try:
        with engine.connect() as conn:
            query = text("""
                SELECT 
                    endurance_goal_distance, 
                    endurance_goal_time,
                    stamina_goal_reps, 
                    stamina_goal_time_per_rep,
                    speed_goal_reps, 
                    speed_goal_distance_per_rep,
                    speed_goal_time_per_rep
                FROM run_data_schema.USER_SCHEDULE_PROGRESS
                WHERE user_id = :user_id AND week_start_date = :week_start_date
            """)
            result = conn.execute(query, {"user_id": user_id, "week_start_date": week_start_date}).fetchone()

            if result:
                # Return user's specific goals if data exists
                return {
                    "Endurance": {
                        "Distance Goal": result[0] or 0,
                        "Time Goal": result[1] or "N/A"
                    },
                    "Stamina": {
                        "Reps": result[2] or 0,
                        "Time per Rep": result[3] or "N/A"
                    },
                    "Speed": {
                        "Reps": result[4] or 0,
                        "Distance per Rep": result[5] or 0,
                        "Time per Rep": result[6] or "N/A"
                    }
                }
            else:
                # Default to Week 1 goals from schedule_df if no user data found
                week_1_data = schedule_df[schedule_df["Week"] == 1].iloc[0]
                return {
                    "Endurance": {
                        "Distance Goal": week_1_data["Endurance Distance (miles)"],
                        "Time Goal": "N/A"
                    },
                    "Stamina": {
                        "Reps": week_1_data["Stamina Reps"],
                        "Time per Rep": week_1_data["Stamina Time per Rep (minutes)"]
                    },
                    "Speed": {
                        "Reps": week_1_data["Speed Reps"],
                        "Distance per Rep": week_1_data["Speed Distance per Rep (miles)"],
                        "Time per Rep": "2'00\""  # Update if there's a specific target time
                    }
                }

    except Exception as e:
        st.error("Error fetching weekly schedule. Please contact support.")
        # Return Week 1 default schedule from schedule_df in case of error
        week_1_data = schedule_df[schedule_df["Week"] == 1].iloc[0]
        return {
            "Endurance": {
                "Distance Goal": week_1_data["Endurance Distance (miles)"],
                "Time Goal": "N/A"
            },
            "Stamina": {
                "Reps": week_1_data["Stamina Reps"],
                "Time per Rep": week_1_data["Stamina Time per Rep (minutes)"]
            },
            "Speed": {
                "Reps": week_1_data["Speed Reps"],
                "Distance per Rep": week_1_data["Speed Distance per Rep (miles)"],
                "Time per Rep": "2'00\""
            }
        }

# Provides a default set of weekly goals for new users
def generate_default_weekly_goals():
    """
    Generates beginner-friendly weekly performance goals for Endurance, Stamina, 
    and Speed based on recommended starting benchmarks. Music BPM is included 
    to help maintain pace.

    :return: Dictionary with initial target values for each run type.
    Error Handling: N/A, static defaults are provided.
    """
    return {
        "endurance_week": {
            "distance": 3.0,         # Distance in miles
            "pace": "11'00\"",       # Suggested pace
            "music_bpm": 130         # Recommended music BPM
        },
        "stamina_week": {
            "time": "16:00",         # Duration in minutes
            "distance": 1.5,         # Suggested distance in miles
            "pace": "10'30\"",       # Suggested pace
            "music_bpm": 140         # Recommended music BPM
        },
        "speed_week": {
            "intervals": 5,          # Number of intervals
            "interval_time": "2:00", # Suggested time per interval
            "pace": "8'30\"",        # Suggested pace per interval
            "music_bpm": 150         # Recommended music BPM
        }
    }

# Function to fetch user run data based on run type
def fetch_run_data(user_id, run_type):
    """
    Fetches a user's run data filtered by run type and displays relevant metrics.
    
    :param user_id: Unique identifier for the user.
    :param run_type: Type of run - 'Endurance', 'Stamina', or 'Speed'.
    :return: DataFrame containing the run data for the specified type.
    """
    with get_engine().connect() as conn:
        if run_type == 'Endurance':
            query = """
                SELECT total_distance, avg_pace, music_bpm, run_date
                FROM run_data
                WHERE user_id = %s AND run_type = %s
            """
        else:
            query = """
                SELECT rep_count, rep_distance, rep_time, avg_pace, music_bpm, run_date
                FROM run_data
                WHERE user_id = %s AND run_type = %s
            """
        
        return pd.read_sql(query, conn, params=(user_id, run_type))

# Logs individual run data into the database
def log_run_data(user_id, run_type, distance=None, avg_pace=None, cadence=None,
                 effort=None, location=None, music_bpm=None, breathing_tempo=None,
                 run_time=None, run_time_seconds=None, reps=None,
                 rep_distance=None, rep_time=None):
    """
    Logs run data for a user based on various metrics, including distance, pace, and 
    unique details for endurance, stamina, and speed runs.

    :param user_id: Unique identifier for the user.
    :param run_type: Type of run ('Endurance', 'Stamina', 'Speed').
    :param distance: Total distance covered (miles).
    :param avg_pace: Average pace as a string, e.g., 'minutes/mile'.
    :param cadence: Steps per minute.
    :param effort: Perceived effort on a scale of 1.0 to 10.0.
    :param location: Location of the run (Street, Track, Trail).
    :param music_bpm: Music beats per minute.
    :param breathing_tempo: Steps per inhale/exhale pattern.
    :param run_time: Duration of the run (optional).
    :param run_time_seconds: Duration in seconds for logging.
    :param reps: Number of repetitions or sets completed.
    :param rep_distance: Distance per repetition, used for interval training.
    :param rep_time: Time per repetition in seconds.
    :return: None
    Error Handling: Logs an error if the data logging fails.
    """
    try:
        with get_engine().connect() as conn:
            query = """
                INSERT INTO run_data (user_id, run_type, distance, avg_pace, cadence, 
                effort, location, music_bpm, breathing_tempo, run_time, run_time_seconds, 
                reps, rep_distance, rep_time)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            conn.execute(query, (user_id, run_type, distance, avg_pace, cadence, effort,
                                 location, music_bpm, breathing_tempo, run_time, 
                                 run_time_seconds, reps, rep_distance, rep_time))
    except Exception as e:
        st.error("Error logging run data. Please try again or contact support.")

# Streamlit UI
st.title("Personal Running Analysis")

# Toggle between Login and Sign Up views
auth_action = st.radio("Choose an action", ["Login", "Sign Up"])

if auth_action == "Login":
    # Login form
    with st.form("login_form"):
        st.write("Please login to continue")
        input_username = st.text_input("Username")
        input_password = st.text_input("Password", type="password")
        submit_button = st.form_submit_button("Login")
    
    if submit_button:
        if authenticate(input_username, input_password):
            st.success("Login successful!")

            # Display Running Schedule Table
            st.subheader("Weekly Running Schedule")
            st.write("This table outlines your planned schedule for endurance, stamina, and speed goals:")
            st.dataframe(schedule_df)

            # Data submission section
            st.subheader("Enter New Run Data")
            st.write("Use the Nike Run Club app to gather your data, then enter the details below.")

            # Dropdown to select the run type
            run_type = st.selectbox("Run Type", ["Endurance", "Stamina", "Speed"])

            # Input fields for run details
            distance = st.number_input("Distance (miles)", min_value=0.0, step=0.01)
            avg_pace = st.text_input("Average Pace (e.g., 7'38\")")
            run_time = st.text_input("Time (e.g., 01:57)")
            cadence = st.number_input("Cadence", min_value=0, step=1)
            effort = st.slider("Effort (1 to 10)", min_value=1.0, max_value=10.0, step=0.5)
            location = st.selectbox("Location", ["Street", "Track", "Trail"])
            music_bpm = st.selectbox("Music BPM", list(range(0, 205, 5)))  # Options in increments of 5
            breathing_tempo = st.text_input("Breathing Tempo (e.g., 2:2 for inhale 2 steps, exhale 2 steps)")

            # Submission button
            submit_data_button = st.button("Submit Data")

            if submit_data_button:
                # Collect data to update the schedule
                run_data = {
                    "endurance": distance if run_type == "Endurance" else 0,
                    "stamina": run_time if run_type == "Stamina" else 0,
                    "speed": cadence if run_type == "Speed" else 0
                }
                check_and_update_schedule(input_username, run_data)
                st.success("Run data submitted and schedule updated successfully!")

            # Data visualization
            st.subheader("Run Analysis")
            with get_engine().connect() as conn:
                query = text("""
                    SELECT run_type, distance, run_time, "Stamina Run (minutes)"
                    FROM run_data
                    WHERE user_id = (SELECT user_id FROM users WHERE username = :username)
                """)
                df = pd.read_sql(query, conn, params={"username": input_username})

            # Parse `Stamina Run (minutes)` column if it exists
            if 'Stamina Run (minutes)' in df.columns:
                df['Stamina Run (minutes)'] = df['Stamina Run (minutes)'].apply(
                    lambda x: {
                        'num_reps': int(x.split('x')[0]),
                        'duration_per_rep': int(x.split('x')[1])
                    } if isinstance(x, str) and 'x' in x else {'num_reps': 1, 'duration_per_rep': int(x) if isinstance(x, str) else x}
                )
                # Convert nested dictionary to separate columns for compatibility
                df = pd.concat([df, pd.json_normalize(df['Stamina Run (minutes)'])], axis=1).drop(columns=['Stamina Run (minutes)'])

            if not df.empty:
                # Plot each run type
                for run in ["Endurance", "Stamina", "Speed"]:
                    run_data = df[df['run_type'] == run]
                    if not run_data.empty:
                        fig, ax = plt.subplots()
                        ax.plot(run_data["distance"], run_data["run_time"], marker='o')
                        ax.set_title(f"{run} Run Analysis")
                        ax.set_xlabel("Distance (km)")
                        ax.set_ylabel("Time (minutes)")
                        st.pyplot(fig)
            else:
                st.write("No data available for this user.")

            # Suggested goals for next week
            st.subheader("Suggested Goals for Next Week")
            user_weeks = get_user_schedule_progress(input_username)
            next_week_goals = {
                "Endurance": get_next_week_goals(user_weeks['endurance_week']),
                "Stamina": get_next_week_goals(user_weeks['stamina_week']),
                "Speed": get_next_week_goals(user_weeks['speed_week'])
            }
            if any(next_week_goals.values()):
                st.write("Next week goals:", next_week_goals)
            else:
                st.write("No goals available for next week.")
        else:
            st.error("Invalid credentials. Please try again.")

elif auth_action == "Sign Up":
    # Sign Up form
    with st.form("signup_form"):
        st.write("Create a new account")
        new_username = st.text_input("New Username")
        new_email = st.text_input("Email")
        new_password = st.text_input("Password", type="password")
        signup_button = st.form_submit_button("Sign Up")
    
    if signup_button:
        try:
            register_user(new_username, new_email, new_password)
            st.success("Account created successfully! Please log in.")
        except Exception as e:
            st.error(f"Error: {str(e)}")
