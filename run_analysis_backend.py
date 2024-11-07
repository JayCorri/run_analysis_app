"""
Run Analysis Backend Functions
Version: 3.1.1

Description:
This module contains the backend functions for the Run Analysis App, including database interactions,
user authentication, data logging, and regimen-specific schedule management.

New Features in v3.1.1:
- **Error Logging to Database**: All backend functions now log errors to a dedicated database table (`error_logs`).
- **Streamlit Feedback**: Errors in backend functions provide immediate feedback in Streamlit for better user experience.

Previous Features in v3.1:
- **Regimen Management**: Retrieves and manages schedules for multiple regimens (e.g., NSW Candidate, Marathon).
- **User Settings Persistence**: Saves and loads user settings for regimen and week, ensuring data consistency across sessions.
- **Goal Tracking**: Defines weekly goals for endurance, stamina, and speed, and updates based on user input.
- **Improved Error Handling**: Enhanced database error reporting and user feedback for seamless experience.

Future Plans:
- Expand support for more complex regimens and training programs.
- Optimize database queries for enhanced performance with larger datasets.
"""



def get_engine():
    """
    Creates and returns a SQLAlchemy engine for Snowflake database connection.

    Error Logging: Logs any connection errors.
    """
    try:
        engine = create_engine(
            f"snowflake://{st.secrets['SNOWFLAKE']['USER']}:{st.secrets['SNOWFLAKE']['PASSWORD']}@{st.secrets['SNOWFLAKE']['ACCOUNT']}/{st.secrets['SNOWFLAKE']['DATABASE']}/{st.secrets['SNOWFLAKE']['SCHEMA']}?warehouse={st.secrets['SNOWFLAKE']['WAREHOUSE']}&role={st.secrets['SNOWFLAKE']['ROLE']}"
        )
        return engine
    except Exception as e:
        error_message = str(e)
        log_error("get_engine", error_message)
        return None  # Return None if there’s a failure to create the engine

# Fetch available training regimens from the database with error handling
def get_available_regimens():
    """
    Retrieves all available training regimens for selection in the app.
    
    :return: DataFrame of regimen_id and regimen_name or an empty DataFrame if an error occurs.
    Error Logging: Logs any database or query errors.
    """
    query = "SELECT regimen_id, regimen_name FROM training_regimens"
    try:
        engine = get_engine()
        if engine is None:
            raise ConnectionError("Failed to create database engine.")
        
        with engine.connect() as conn:
            regimens = pd.read_sql(query, conn)
        return regimens
    except Exception as e:
        error_message = str(e)
        log_error("get_available_regimens", error_message, parameters={"query": query})
        return pd.DataFrame(columns=["regimen_id", "regimen_name"])  # Return empty DataFrame if an error occurs

#
# commented out, duplicate function. saved in case of error to compare against active version
# 
# def get_available_regimens():
    # Assuming you are using SQLAlchemy to fetch regimens
    query = text("SELECT regimen_id, regimen_name FROM training_regimens")
    with get_engine().connect() as conn:
        result = conn.execute(query).fetchall()
        # Convert to DataFrame to handle columns properly
        regimens_df = pd.DataFrame(result, columns=['regimen_id', 'regimen_name'])
    return regimens_df
#
  
# Register a new user with hashed password and error handling
def register_user(username, email, password):
    """
    Registers a new user by storing a username, email, and base64-encoded hashed password in the database.
    
    :param username: Unique identifier for the user.
    :param email: User's email address for login and recovery.
    :param password: Raw password which is hashed and base64-encoded before storing.
    :return: None
    Error Logging: Logs errors encountered during hashing, encoding, or database insertion.
    Note: Password hash is base64-encoded for compatibility with Snowflake VARCHAR storage.
    """
    try:
        # Hash the password
        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        
        # Convert binary hash to base64-encoded string for VARCHAR storage
        hashed_pw_str = base64.b64encode(hashed_pw).decode('utf-8')
        
        # Store in Snowflake as VARCHAR using SQLAlchemy engine
        engine = get_engine()
        if engine is None:
            raise ConnectionError("Failed to create database engine.")
        
        with engine.connect() as conn:
            conn.execute(
                text("""
                    INSERT INTO users (username, email, password_hash) 
                    VALUES (:username, :email, :password_hash)
                """),
                {"username": username, "email": email, "password_hash": hashed_pw_str}
            )
    except Exception as e:
        error_message = str(e)
        log_error("register_user", error_message, parameters={"username": username, "email": email})

# Authenticate user by verifying hashed password in database with error handling
def authenticate(username, password):
    """
    Authenticates a user by checking their base64-encoded hashed password in the database.
    
    :param username: Username for login.
    :param password: Plaintext password to verify against stored hash.
    :return: Boolean indicating whether authentication is successful.
    Error Logging: Logs errors encountered during database retrieval or password verification.
    Note: Password hash is decoded from base64 back to binary before verification.
    """
    try:
        engine = get_engine()
        if engine is None:
            raise ConnectionError("Failed to create database engine.")
        
        query = text("SELECT password_hash FROM users WHERE username = :username")
        
        with engine.connect() as conn:
            result = conn.execute(query, {"username": username}).fetchone()
            
            if result:
                # Decode the base64 stored hash back to binary
                stored_hash = base64.b64decode(result[0])
                return bcrypt.checkpw(password.encode('utf-8'), stored_hash)
            else:
                # Log if username is not found in the database
                log_error("authenticate", "Username not found", parameters={"username": username})
                return False
                
    except Exception as e:
        error_message = str(e)
        log_error("authenticate", error_message, parameters={"username": username})
        return False

# Function to send a password recovery email with error handling
def send_recovery_email(email, username, recovery_link):
    """
    Sends an email to the user with their username and a password reset link for recovery.

    :param email: The registered email address of the user.
    :param username: The user's username for personalization.
    :param recovery_link: The link for password recovery.
    :return: None
    Error Logging: Logs issues with email setup, server connection, and email dispatch.
    """
    try:
        # Prepare email content
        msg = MIMEText(f"Hello {username},\n\nClick here to reset your password: {recovery_link}")
        msg["Subject"] = "Password Recovery"
        msg["From"] = st.secrets["EMAIL"]["FROM_EMAIL"]
        msg["To"] = email

        # Attempt to send the email
        with smtplib.SMTP(st.secrets["EMAIL"]["SMTP_SERVER"], st.secrets["EMAIL"]["SMTP_PORT"]) as server:
            server.login(st.secrets["EMAIL"]["USER"], st.secrets["EMAIL"]["PASSWORD"])
            server.sendmail(st.secrets["EMAIL"]["USER"], email, msg.as_string())
        
    except smtplib.SMTPException as e:
        # Log SMTP-specific errors
        log_error("send_recovery_email", f"SMTP error: {str(e)}", parameters={"email": email, "username": username})
    except Exception as e:
        # Log other potential errors
        log_error("send_recovery_email", f"General error: {str(e)}", parameters={"email": email, "username": username})

# Retrieves the user's schedule progress for endurance, stamina, and speed
def get_user_schedule_progress(username):
    """
    Retrieves the user's schedule progress for endurance, stamina, and speed.

    :param username: Unique identifier for the user.
    :return: Dictionary with progress data or default values if no data exists.
    Error Handling: Returns default values if database access fails and logs detailed error info.
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
        # Enhanced error logging with function details
        log_error(
            function_name="get_user_schedule_progress",
            error_message=str(e),
            parameters={"username": username}
        )
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
    Error Handling: Safely increments the specified category's week in the database and logs errors.
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
        # Enhanced error logging with function details
        log_error(
            function_name="update_user_schedule_progress",
            error_message=str(e),
            parameters={"username": username, "category": category}
        )

# Checks if user met weekly goals and updates progress if achieved
def check_and_update_schedule(username, run_data):
    """
    Checks if the user met the scheduled goal and updates their week if achieved.

    :param username: Username of the user.
    :param run_data: Dictionary with user input for endurance, stamina, and speed data.
    :return: None
    Error Handling: Logs errors if there are issues with fetching scheduled goals or updating progress.
    """
    try:
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

    except Exception as e:
        # Log error with relevant details for troubleshooting
        log_error(
            function_name="check_and_update_schedule",
            error_message=str(e),
            parameters={"username": username, "run_data": run_data}
        )

# Helper function to retrieve weekly goals from Snowflake with error logging
def get_weekly_goal_for_run_type(run_type, week):
    """
    Retrieves the goal for a specific run type and week from Snowflake.
    
    :param run_type: The type of run (e.g., "endurance", "stamina", "speed").
    :param week: The week number for which to retrieve the goal.
    :return: The scheduled goal for the specified run type and week.
    """
    try:
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

    except Exception as e:
        log_error("get_weekly_goal_for_run_type", str(e), run_type=run_type, week=week)
        return None

# Function to retrieve the next week's goals based on regimen and week structure with error logging
def get_next_week_goals(current_week, regimen_id):
    """
    Retrieves the next week's goals based on the regimen and week structure.
    
    :param current_week: The user's current week number.
    :param regimen_id: The ID of the regimen to look up.
    :return: Dictionary with goals for endurance, stamina, and speed or None if no data is available.
    """
    try:
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

    except Exception as e:
        log_error("get_next_week_goals", str(e), current_week=current_week, regimen_id=regimen_id)
        return None

# Function to display the weekly running schedule goal and performance for the selected run type with error logging
def display_run_goal_and_performance(run_type, weekly_schedule):
    """
    Displays the goal and performance metrics for the selected run type.

    :param run_type: Selected run type (Endurance, Stamina, Speed).
    :param weekly_schedule: Dictionary containing weekly goals and performance metrics.
    :return: None
    Error Handling: Displays default text if metrics are missing, logs error if issues occur.
    """
    try:
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
    
    except Exception as e:
        log_error("display_run_goal_and_performance", str(e), run_type=run_type, weekly_schedule=weekly_schedule)
        st.write("Error displaying run goal and performance. Please try again or contact support.")

# Function to display the weekly running schedule with options for toggling between run types with error logging
def weekly_schedule_view(weekly_schedule):
    """
    Displays the weekly running schedule with options to view goals and performance by run type.

    :param weekly_schedule: Dictionary containing goals and current performance data for each run type.
    :return: None
    Error Handling: Handles missing or incomplete data gracefully, logs error if issues occur.
    """
    try:
        st.header("Weekly Running Schedule")
        
        # Toggle menu for selecting Endurance, Stamina, or Speed
        run_type = st.radio("Select Run Type", ("Endurance", "Stamina", "Speed"))
        
        # Display selected run type's goals and performance
        display_run_goal_and_performance(run_type, weekly_schedule)
    
    except Exception as e:
        log_error("weekly_schedule_view", str(e), weekly_schedule=weekly_schedule)
        st.write("Error displaying weekly schedule. Please try again or contact support.")

# Function to retrieve the user's weekly schedule based on regimen, week, and specific month criteria
def get_user_weekly_schedule(user_id):
    """
    Retrieves the weekly schedule for the user based on regimen, current week, and whether
    it is the first, last, or mid-month week in Marathon regimen.
    
    :param user_id: Unique identifier for the user.
    :return: DataFrame with weekly schedule or None if retrieval fails.
    Error Handling: Logs error if any issues occur during data retrieval.
    """
    try:
        with get_engine().connect() as conn:
            user_data = conn.execute(text("""
                SELECT regimen_id, current_week
                FROM users
                WHERE user_id = :user_id
            """), {"user_id": user_id}).fetchone()
            
            if not user_data:
                raise ValueError("User data not found for the provided user_id.")

            regimen_id = user_data['regimen_id']
            current_week = user_data['current_week']
            today = datetime.today()
            
            # Determine the week type for the Marathon regimen
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
            
            else:
                raise ValueError("Invalid regimen ID detected in user data.")
            
            return schedule

    except Exception as e:
        log_error("get_user_weekly_schedule", str(e), user_id=user_id)
        st.write("Error retrieving the user's weekly schedule. Please try again or contact support.")
        return None

# Function to generate default weekly goals for new users
def generate_default_weekly_goals():
    """
    Generates beginner-friendly weekly performance goals for Endurance, Stamina, 
    and Speed based on recommended starting benchmarks. Music BPM is included 
    to help maintain pace.

    :return: Dictionary with initial target values for each run type.
    Error Handling: Captures any unexpected error and logs it, though defaults are static.
    """
    try:
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
    except Exception as e:
        log_error("generate_default_weekly_goals", str(e))
        st.write("Error generating default weekly goals. Please try again or contact support.")
        return None

# Function to fetch user run data based on run type
def fetch_run_data(user_id, run_type):
    """
    Fetches a user's run data filtered by run type and displays relevant metrics.
    
    :param user_id: Unique identifier for the user.
    :param run_type: Type of run - 'Endurance', 'Stamina', or 'Speed'.
    :return: DataFrame containing the run data for the specified type.
    Error Handling: Logs any error and returns an empty DataFrame if fetching fails.
    """
    try:
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
            
            # Execute query and fetch data
            return pd.read_sql(query, conn, params=(user_id, run_type))
    
    except Exception as e:
        log_error("fetch_run_data", str(e))
        st.write("Error fetching run data. Please try again or contact support.")
        # Return an empty DataFrame to avoid breaking the app
        return pd.DataFrame()

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
        log_error("log_run_data", str(e))  # Log the error
        st.write("Error logging run data. Please try again or contact support.")

# Retrieve available training regimens from Snowflake
def get_available_regimens():
    """
    Fetches available regimens from the training_regimens table in Snowflake.
    
    :return: DataFrame with regimen_id and regimen_name.
    Error Handling: Logs an error and returns an empty DataFrame if no regimens are found or a database error occurs.
    """
    try:
        query = "SELECT regimen_id, regimen_name FROM training_regimens"
        with get_engine().connect() as conn:
            regimens = pd.read_sql(query, conn)
        return regimens
    except Exception as e:
        log_error("get_available_regimens", str(e), {"query": query})
        return pd.DataFrame()  # Return an empty DataFrame on error

# Retrieve the schedule for a specific training regimen
def get_regimen_schedule(regimen_id):
    """
    Fetches weekly schedule details for the selected training regimen.
    
    :param regimen_id: The ID of the selected training regimen.
    :return: DataFrame with weekly schedule data for the specified regimen.
    Error Handling: Logs an error and returns an empty DataFrame if regimen ID is not found or a database error occurs.
    """
    query = f"""
        SELECT week, endurance_distance, stamina_reps, stamina_time_per_rep, 
               speed_reps, speed_distance_per_rep
        FROM schedules
        WHERE regimen_id = {regimen_id}
        ORDER BY week
    """
    try:
        with get_engine().connect() as conn:
            schedule_df = pd.read_sql(query, conn)
        return schedule_df
    except Exception as e:
        log_error("get_regimen_schedule", str(e), {"regimen_id": regimen_id, "query": query})
        return pd.DataFrame()  # Return an empty DataFrame on error

# Update the user's regimen and current week in the database
def update_user_settings(username, regimen_id, current_week):
    """
    Updates the user's selected regimen and current week in the database.
    
    :param username: The user's unique identifier.
    :param regimen_id: The ID of the selected regimen.
    :param current_week: The current week to be set.
    :return: None
    Error Handling: Logs any database errors and provides feedback to the user.
    """
    query = text("""
        UPDATE users
        SET regimen_id = :regimen_id, current_week = :current_week
        WHERE username = :username
    """)

    try:
        with get_engine().connect() as conn:
            conn.execute(query, {
                "regimen_id": regimen_id,
                "current_week": current_week,
                "username": username
            })
        
        # Update session state to reflect the changes for in-session use
        st.session_state['regimen_id'] = regimen_id
        st.session_state['current_week'] = current_week
    
    except Exception as e:
        log_error("update_user_settings", str(e), {
            "username": username,
            "regimen_id": regimen_id,
            "current_week": current_week
        })

# Load the user's regimen and week settings from the database on login
def load_user_settings(username):
    """
    Loads the user's saved regimen and week settings from Snowflake on login.
    
    :param username: The user's unique identifier.
    :return: None
    Error Handling: Logs an error if data retrieval fails or is incomplete, and sets default values if no data found.
    """
    try:
        with get_engine().connect() as conn:
            query = text("""
                SELECT regimen_id, current_week
                FROM users
                WHERE username = :username
            """)
            user_settings = conn.execute(query, {"username": username}).fetchone()
            
            # Debugging: log user_settings to check the content and structure
            print(f"Loaded user settings for {username}: {user_settings}")

            # Check if user_settings is not None and contains expected elements
            if user_settings is not None and len(user_settings) >= 2:
                st.session_state['regimen_id'] = user_settings[0]  # regimen_id
                st.session_state['current_week'] = user_settings[1]  # current_week
            else:
                # Default values if user settings are not found or incomplete
                st.session_state['regimen_id'] = 101
                st.session_state['current_week'] = 1

    except Exception as e:
        error_message = str(e)
        log_error("load_user_settings", error_message, {"username": username})

# Authenticate and log the user in, loading settings upon success
def login_user(username, password):
    """
    Authenticates the user and loads saved regimen and week settings on successful login.
    
    :param username: The user's unique identifier.
    :param password: The user's password to be authenticated.
    :return: None
    Error Handling: Logs an error if authentication or settings load fails.
    """
    try:
        if authenticate(username, password):
            st.session_state['is_logged_in'] = True
            st.session_state['username'] = username
            load_user_settings(username)  # Load user's regimen and week settings from Snowflake
            st.success("Login successful!")
        else:
            st.error("Invalid username or password.")
    except Exception as e:
        error_message = str(e)
        log_error("login_user", error_message, {"username": username})
        st.error("An error occurred during login. Please try again or contact support.")

# Logs out the user by clearing session state data
def logout_user():
    """
    Logs out the user and clears session state data.
    
    :return: None
    Error Handling: Logs an error if the session state cannot be cleared.
    """
    try:
        st.session_state['is_logged_in'] = False
        st.session_state.clear()  # Clear session state data on logout
        st.success("Logout successful!")
    except Exception as e:
        error_message = str(e)
        log_error("logout_user", error_message)
        st.error("An error occurred during logout. Please try again or contact support.")

# log errors to snowflake and streamlit 
def log_error(function_name, error_message, parameters=None):
    """
    Logs error details to the database with function name, error message, and parameters.
    
    :param function_name: Name of the function where the error occurred.
    :param error_message: Description of the error.
    :param parameters: Optional dictionary of parameters related to the function call.
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    param_str = str(parameters) if parameters else "None"
    
    # Logging to console for initial setup (replace with database connection in production)
    print(f"[{timestamp}] Error in {function_name}: {error_message} | Params: {param_str}")
    
    # Optional: log to Snowflake or another DB
    query = text("""
        INSERT INTO error_logs (timestamp, function_name, error_message, parameters)
        VALUES (:timestamp, :function_name, :error_message, :parameters)
    """)
    
    st.error(f"""
             An error occurred in {function_name}. Please try again or contact support.
             Details:
             - Timestamp: {datetime.now()}
             - Function: {function_name}
             - Error Message: {error_message}
             - Parameters: {param_str}
             """)

    with get_engine().connect() as conn:
        conn.execute(query, {
            "timestamp": timestamp,
            "function_name": function_name,
            "error_message": error_message,
            "parameters": param_str
        })
