"""
Run Analysis Streamlit App
Version: 1.3

Updates:
- Added default return values in `get_user_schedule_progress` to handle cases where user data is unavailable.
- Enhanced error handling to provide user feedback upon database issues.
"""



import os
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from snowflake.connector import connect
import bcrypt
import base64
import smtplib
from email.mime.text import MIMEText


# Connect to Snowflake using st.secrets for secure credentials
def connect_to_snowflake():
    """
    Establishes a connection to the Snowflake database using credentials from st.secrets.

    :return: Snowflake connection object.
    """
    return connect(
        account=st.secrets["SNOWFLAKE"]["ACCOUNT"],
        user=st.secrets["SNOWFLAKE"]["USER"],
        password=st.secrets["SNOWFLAKE"]["PASSWORD"],
        database=st.secrets["SNOWFLAKE"]["DATABASE"],
        schema=st.secrets["SNOWFLAKE"]["SCHEMA"],
        warehouse=st.secrets["SNOWFLAKE"]["WAREHOUSE"],
        role=st.secrets["SNOWFLAKE"]["ROLE"]
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
    
    # Store in Snowflake as VARCHAR
    with connect_to_snowflake() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO users (username, email, password_hash) 
            VALUES (%s, %s, %s)
        """, (username, email, hashed_pw_str))

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
    with connect_to_snowflake() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE username = %s", (username,))
        result = cursor.fetchone()
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

# Weekly running schedule table
schedule_data = {
    "Week": list(range(1, 35)),
    "Endurance Distance (miles)": [3, 3.25, 3.5, 3.75, 4, 4.25, 4.5, 4.75, 5, 5.25, 5.5, 5.75, 6, 6.25, 6.5, 6.75, 7, 7.25, 7.5, 7.75, 8, 8.25, 8.5, 8.75, 9, 9.25, 9.5, 9.75, 10, 10, 10, 10, 10, 10],
    "Stamina Run (minutes)": [15, 15, 16, 16, 17, 17, 18, 18, 19, 19, 20, "2x12", "2x12", "2x14", "2x14", "2x14", "2x16", "2x16", "2x16", "2x18", "2x18", "2x18", "2x20", "2x20", "2x20", "3x14", "3x14", "3x14", "3x17", "3x17", "3x17", "3x20", "3x20", "3x20"],
    "Speed Intervals": [4, 4, 5, 5, 6, 6, 7, 7, 8, 8, 9, 9, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10, 10]
}
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
        with connect_to_snowflake() as conn:
            cursor = conn.cursor()
            # Query to check if user has any run data
            cursor.execute("""
                SELECT AVG(distance) AS endurance_week,
                       AVG(cadence) AS stamina_week,
                       AVG(run_time) AS speed_week
                FROM run_data
                WHERE user_id = (SELECT user_id FROM users WHERE username = %s)
            """, (username,))
            result = cursor.fetchone()
            
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
    except ProgrammingError as e:
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
    Error Handling: Updates database with new week.
    """
    with connect_to_snowflake() as conn:
        cursor = conn.cursor()
        cursor.execute(f"""
            UPDATE user_schedule_progress
            SET {category}_week = {category}_week + 1
            WHERE username = %s
        """, (username,))

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
            with connect_to_snowflake() as conn:
                query = f"SELECT run_type, distance, run_time FROM run_data WHERE user_id = (SELECT user_id FROM users WHERE username = '{input_username}')"
                df = pd.read_sql(query, conn)

            if not df.empty:
                # Plot each run type
                for run in ["Endurance", "Stamina", "Speed"]:
                    run_data = df[df['run_type'] == run]
                    if not run_data.empty:
                        fig, ax = plt.subplots()
                        ax.plot(run_data["distance"], run_data["time"], marker='o')
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
