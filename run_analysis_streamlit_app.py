"""
Run Analysis Streamlit App
Version: 2.1

Description:
This application tracks user run metrics with support for multiple training regimens.
New Features:
- Integrated regimen selection from the unified 'schedules' table
- Default regimen set to NSW Candidate Run Regimen, with option for Marathon Trainer Regimen
- Structured to allow easy addition of future training regimens
"""



from sqlalchemy import create_engine, text
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
import bcrypt
import base64
import smtplib
from email.mime.text import MIMEText
from datetime import datetime
from datetime import timedelta
import calendar

# Set initial session variables
if 'is_logged_in' not in st.session_state:
    st.session_state['is_logged_in'] = False
if 'auth_action' not in st.session_state:
    st.session_state['auth_action'] = "Login"  # Default to Login view

def get_engine():
    return create_engine(
        f"snowflake://{st.secrets['SNOWFLAKE']['USER']}:{st.secrets['SNOWFLAKE']['PASSWORD']}@{st.secrets['SNOWFLAKE']['ACCOUNT']}/{st.secrets['SNOWFLAKE']['DATABASE']}/{st.secrets['SNOWFLAKE']['SCHEMA']}?warehouse={st.secrets['SNOWFLAKE']['WAREHOUSE']}&role={st.secrets['SNOWFLAKE']['ROLE']}"
    )

# Fetch available training regimens from the database
def get_available_regimens():
    """
    Retrieves all available training regimens for selection in the app.
    
    :return: DataFrame of regimen_id and regimen_name.
    """
    query = "SELECT regimen_id, regimen_name FROM training_regimens"
    with get_engine().connect() as conn:
        regimens = pd.read_sql(query, conn)
    return regimens
   
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

def check_and_update_schedule(username, run_data):
    """
    Checks if the user met the scheduled goal and updates their week if achieved.
    """
    # Retrieve user’s regimen ID and week goals
    regimen_id = st.session_state.get('regimen_id')  # Adjust based on where regimen_id is stored
    user_weeks = get_user_weekly_schedule(username)

    for run_type in ["endurance", "stamina", "speed"]:
        week_goal = user_weeks[f"{run_type}_week"]

        # SQL fetch to validate goal completion
        query = text("""
            SELECT * FROM schedules WHERE regimen_id = :regimen_id AND week = :week
        """)
        
        # Execute query with regimen_id and week_goal
        with get_engine().connect() as conn:
            scheduled_goal_df = pd.read_sql(query, conn, params={"regimen_id": regimen_id, "week": week_goal})
        
        # Validate that scheduled_goal_df is not empty and fetch goal
        if not scheduled_goal_df.empty:
            scheduled_goal = scheduled_goal_df[f"{run_type}_goal_column"].iloc[0]  # Replace `run_type` with specific goal column
            # Check if the user's run data meets or exceeds the scheduled goal
            if run_data[run_type] >= scheduled_goal:
                update_user_schedule_progress(username, f"{run_type}_week")

# Helper function to retrieve weekly goals from Snowflake
def get_weekly_goal_for_run_type(run_type, week):
    """
    Retrieves the goal for a specific run type and week from Snowflake.
    :param run_type: The type of run (e.g., "endurance", "stamina", "speed").
    :param week: The week number for which to retrieve the goal.
    :return: The scheduled goal for the specified run type and week.
    """
    # Map run type to corresponding Snowflake column names
    column_map = {
        "endurance": "endurance_distance",
        "stamina": "stamina_reps", 
        "speed": "speed_reps"
    }
    column_name = column_map[run_type]

    query = f"""
        SELECT {column_name}
        FROM schedules
        WHERE week = :week AND regimen_id = 101  -- Assuming NSW Candidate Regimen ID is 101
    """
    with get_engine().connect() as conn:
        result = conn.execute(query, {"week": week}).fetchone()
        
    return result[0] if result else None

def get_next_week_goals(current_week, regimen_id):
    """
    Retrieves the next week's goals based on the regimen and week structure.
    """
    with get_engine().connect() as conn:
        query = text("""
            SELECT endurance_distance, stamina_reps, stamina_time_per_rep,
                   speed_reps, speed_distance_per_rep
            FROM schedules
            WHERE regimen_id = :regimen_id AND week = :next_week
        """)
        result = conn.execute(query, {"regimen_id": regimen_id, "next_week": current_week + 1}).fetchone()
        
        if result:
            return {
                "Endurance Distance": result[0] or 0,
                "Stamina Run Duration": result[1] or "N/A",
                "Speed Intervals": result[2] or "N/A"
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

def get_user_weekly_schedule(user_id):
    """
    Retrieves the weekly schedule for the user based on regimen, current week, and whether
    it is the first, last, or mid-month week in Marathon regimen.
    """
    with get_engine().connect() as conn:
        user_data = conn.execute(text("""
            SELECT regimen_id, current_week
            FROM users
            WHERE user_id = :user_id
        """), {"user_id": user_id}).fetchone()
        
        regimen_id = user_data['regimen_id']
        current_week = user_data['current_week']
        today = datetime.today()
        
        # Determine Marathon regimen week type
        if regimen_id == 102:  # Marathon
            if today.day <= 7:
                schedule_id = 101  # Marathon Week
            elif today >= (today.replace(day=1) + timedelta(days=31)).replace(day=1) - timedelta(days=1):
                schedule_id = 103  # Short and Fast Week
            else:
                schedule_id = 102  # Normal Week
            query = text("""
                SELECT *
                FROM schedules
                WHERE regimen_id = :regimen_id AND schedule_id = :schedule_id
            """)
            schedule = pd.read_sql(query, conn, params={"regimen_id": regimen_id, "schedule_id": schedule_id})
        
        elif regimen_id == 101:  # NSW regimen sequential weeks
            query = text("""
                SELECT *
                FROM schedules
                WHERE regimen_id = :regimen_id AND week = :current_week
            """)
            schedule = pd.read_sql(query, conn, params={"regimen_id": regimen_id, "current_week": current_week})

    return schedule

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

# Retrieve available training regimens from Snowflake
def get_available_regimens():
    """
    Fetches available regimens from the training_regimens table in Snowflake.
    
    :return: DataFrame with regimen_id and regimen_name.
    Error Handling: Returns empty DataFrame if no regimens are found.
    """
    query = "SELECT regimen_id, regimen_name FROM training_regimens"
    with get_engine().connect() as conn:
        regimens = pd.read_sql(query, conn)
    return regimens

# Retrieve the schedule for a specific training regimen
def get_regimen_schedule(regimen_id):
    """
    Fetches weekly schedule details for the selected training regimen.
    
    :param regimen_id: The ID of the selected training regimen.
    :return: DataFrame with weekly schedule data for the specified regimen.
    Error Handling: Returns empty DataFrame if regimen ID is not found.
    """
    query = f"""
        SELECT week, endurance_distance, stamina_reps, stamina_time_per_rep, 
               speed_reps, speed_distance_per_rep
        FROM schedules
        WHERE regimen_id = {regimen_id}
        ORDER BY week
    """
    with get_engine().connect() as conn:
        schedule_df = pd.read_sql(query, conn)
    return schedule_df

def update_user_settings(username, regimen_id, current_week):
    """
    Updates the user's selected regimen and current week in the database.
    """
    with get_engine().connect() as conn:
        query = text("""
            UPDATE users
            SET regimen_id = :regimen_id, current_week = :current_week
            WHERE username = :username
        """)
        conn.execute(query, {"regimen_id": regimen_id, "current_week": current_week, "username": username})
    
    # Update session state to reflect the changes for in-session use
    st.session_state['regimen_id'] = regimen_id
    st.session_state['current_week'] = current_week

def load_user_settings(username):
    """
    Loads the user's saved regimen and week settings from Snowflake on login.
    """
    with get_engine().connect() as conn:
        query = text("""
            SELECT regimen_id, current_week
            FROM users
            WHERE username = :username
        """)
        user_settings = conn.execute(query, {"username": username}).fetchone()
        
        # Set session state with saved settings or default to NSW regimen and Week 1
        st.session_state['regimen_id'] = user_settings['regimen_id'] if user_settings else 101
        st.session_state['current_week'] = user_settings['current_week'] if user_settings else 1

def login_user(username, password):
    if authenticate(username, password):  # Replace with actual authentication function
        st.session_state['is_logged_in'] = True
        st.session_state['username'] = username
        load_user_settings(username)  # Load user's regimen and week settings from Snowflake
        st.success("Login successful!")
    else:
        st.error("Invalid username or password.")

def logout_user():
    st.session_state['is_logged_in'] = False
    st.session_state.clear()  # Clear session state data on logout

#Streamlit UI

def main_app_ui():
    st.header("Welcome to the Run Analysis App!")
    
    # Regimen Selection
    regimen_options = ["NSW Candidate", "Marathon Trainer"]
    selected_regimen = st.selectbox(
        "Select Training Regimen", regimen_options,
        index=0 if st.session_state['regimen_id'] == 101 else 1
    )
    new_regimen_id = 101 if selected_regimen == "NSW Candidate" else 102
    
    # Week Selection
    selected_week = st.number_input(
        "Select Week", min_value=1, max_value=34 if new_regimen_id == 101 else 3,
        value=st.session_state['current_week']
    )

    # Update database and session state if regimen or week changes
    if new_regimen_id != st.session_state['regimen_id'] or selected_week != st.session_state['current_week']:
        update_user_settings(st.session_state['username'], new_regimen_id, selected_week)
        st.experimental_rerun()

    # Weekly Schedule and Run Data Input
    display_schedule_and_goals(st.session_state['regimen_id'], st.session_state['current_week'])

    st.subheader("Enter New Run Data")
    run_type = st.selectbox("Run Type", ["Endurance", "Stamina", "Speed"])
    distance = st.number_input("Distance (miles)", min_value=0.0, step=0.01)
    avg_pace = st.text_input("Average Pace (e.g., 7'38\")")
    run_time = st.text_input("Time (e.g., 01:57)")
    cadence = st.number_input("Cadence", min_value=0, step=1)
    effort = st.slider("Effort (1 to 10)", min_value=1.0, max_value=10.0, step=0.5)
    location = st.selectbox("Location", ["Street", "Track", "Trail"])
    music_bpm = st.selectbox("Music BPM", list(range(0, 205, 5)))
    breathing_tempo = st.text_input("Breathing Tempo (e.g., 2:2)")

    if st.button("Submit Data"):
        run_data = {
            "endurance": distance if run_type == "Endurance" else 0,
            "stamina": run_time if run_type == "Stamina" else 0,
            "speed": cadence if run_type == "Speed" else 0
        }
        check_and_update_schedule(st.session_state['username'], run_data)
        st.success("Run data submitted and schedule updated successfully!")

    # Log Out Button
    if st.button("Logout"):
        logout_user()
        st.experimental_rerun()

# Helper function: Display schedule and goals
def display_schedule_and_goals(regimen_id, current_week):
    st.subheader(f"Weekly Running Schedule for Week {current_week}")
    schedule = get_regimen_schedule(regimen_id)
    st.dataframe(schedule)

    st.subheader("Suggested Goals for Next Week")
    user_weeks = get_user_schedule_progress(st.session_state['username'])
    next_week_goals = {
        "Endurance": get_next_week_goals(user_weeks['endurance_week']),
        "Stamina": get_next_week_goals(user_weeks['stamina_week']),
        "Speed": get_next_week_goals(user_weeks['speed_week'])
    }
    if any(next_week_goals.values()):
        st.write("Next week goals:", next_week_goals)
    else:
        st.write("No goals available for next week.")

# Authentication (Login or Sign Up) Views
if not st.session_state['is_logged_in']:
    st.title("Personal Running Analysis")

    # Choose between Login and Sign Up
    auth_action = st.radio("Choose an action", ["Login", "Sign Up"])

    if auth_action == "Login":
        with st.form("login_form"):
            st.header("Login")
            input_username = st.text_input("Username")
            input_password = st.text_input("Password", type="password")
            submit_button = st.form_submit_button("Login")
        
        if submit_button:
            if authenticate(input_username, input_password):
                st.session_state['is_logged_in'] = True
                st.session_state['username'] = input_username
                load_user_settings(input_username)  # Load saved user settings
                st.experimental_rerun()
            else:
                st.error("Invalid credentials. Please try again.")
    
    elif auth_action == "Sign Up":
        with st.form("signup_form"):
            st.header("Sign Up")
            new_username = st.text_input("New Username")
            new_email = st.text_input("Email")
            new_password = st.text_input("Password", type="password")
            signup_button = st.form_submit_button("Sign Up")
        
        if signup_button:
            try:
                register_user(new_username, new_email, new_password)
                st.success("Account created successfully! Please log in.")
                st.session_state['auth_action'] = "Login"
            except Exception as e:
                st.error(f"Error: {str(e)}")

else:
    # If logged in, display the main app content
    main_app_ui()
