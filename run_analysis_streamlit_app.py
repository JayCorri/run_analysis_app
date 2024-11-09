"""
Run Analysis Streamlit App
Version: 3.1.1

Description:
This application tracks user run metrics with support for multiple training regimens, allowing users to
choose between predefined schedules and save progress across sessions. The app interface enables 
users to select a training regimen, log run data, and view weekly goals.

New Features in v3.1.1:
- **Error Notifications**: Each backend error triggers a detailed user-friendly message within the Streamlit app.
- **Error Logging**: Backend functions log errors to a database table and provide Streamlit feedback.

Previous Features in v3.1:
- **Session Persistence**: Users' regimen and current week settings are saved and loaded across sessions.
- **Modular Structure**: Backend functions moved to a separate file (`run_analysis_backend.py`) for improved maintainability.
- **Enhanced Regimen Selection**: Integrated regimen selection with default set to NSW Candidate or Marathon Trainer.
- **Weekly Schedule Display**: Provides weekly goals and suggested targets based on selected regimen and user progress.

Future Plans:
- Support additional custom regimens and extended data visualization.
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
import run_analysis_backend as backend


# Set initial session variables
if 'is_logged_in' not in st.session_state:
    st.session_state['is_logged_in'] = False
if 'auth_action' not in st.session_state:
    st.session_state['auth_action'] = "Login"  # Default to Login view
if 'regimen_id' not in st.session_state:
    st.session_state['regimen_id'] = 101  # Default to NSW Candidate regimen
if 'current_week' not in st.session_state:
    st.session_state['current_week'] = 1  # Default starting week
if 'trigger_rerun' in st.session_state and st.session_state['trigger_rerun']:
    st.session_state['trigger_rerun'] = False

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
        backend.update_user_settings(st.session_state['username'], new_regimen_id, selected_week)

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
        backend.check_and_update_schedule(st.session_state['username'], run_data)
        st.success("Run data submitted and schedule updated successfully!")

    # Log Out Button
    if st.button("Logout"):
        backend.logout_user()

# Helper function: Display schedule and goals
def display_schedule_and_goals(regimen_id, current_week):
    st.subheader(f"Weekly Running Schedule for Week {current_week}")
    schedule = backend.get_regimen_schedule(regimen_id)
    st.dataframe(schedule)

    st.subheader("Suggested Goals for Next Week")
    user_weeks = backend.get_user_schedule_progress(st.session_state['username'])
    user_regimen = st.session_state['regimen_id']
    next_week_goals = {
        "Endurance": backend.get_next_week_goals(user_weeks['endurance_week'], user_regimen),
        "Stamina": backend.get_next_week_goals(user_weeks['stamina_week'], user_regimen),
        "Speed": backend.get_next_week_goals(user_weeks['speed_week'], user_regimen)
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
            if backend.authenticate(input_username, input_password):
                st.session_state['is_logged_in'] = True
                st.session_state['username'] = input_username
                backend.load_user_settings(input_username)  # Load saved user settings
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
                backend.register_user(new_username, new_email, new_password)
                st.success("Account created successfully! Please log in.")
                st.session_state['auth_action'] = "Login"
            except Exception as e:
                st.error(f"Error: {str(e)}")

else:
    # If logged in, display the main app content
    main_app_ui()
