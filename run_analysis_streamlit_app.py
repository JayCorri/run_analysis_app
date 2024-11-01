import os
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from snowflake.connector import connect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Snowflake connection settings
SNOWFLAKE_ACCOUNT = os.getenv("SNOWFLAKE_ACCOUNT")
SNOWFLAKE_USER = os.getenv("SNOWFLAKE_USER")
SNOWFLAKE_PASSWORD = os.getenv("SNOWFLAKE_PASSWORD")
SNOWFLAKE_DATABASE = os.getenv("SNOWFLAKE_DATABASE")
SNOWFLAKE_SCHEMA = os.getenv("SNOWFLAKE_SCHEMA")
SNOWFLAKE_WAREHOUSE = os.getenv("SNOWFLAKE_WAREHOUSE")

# User login credentials
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

# Function to authenticate user
def authenticate(username, password):
    return username == USERNAME and password == PASSWORD

# Function to connect to Snowflake
def connect_to_snowflake():
    conn = connect(
        account=SNOWFLAKE_ACCOUNT,
        user=SNOWFLAKE_USER,
        password=SNOWFLAKE_PASSWORD,
        database=SNOWFLAKE_DATABASE,
        schema=SNOWFLAKE_SCHEMA,
        warehouse=SNOWFLAKE_WAREHOUSE
    )
    return conn

# Streamlit UI
st.title("Personal Running Analysis")

# Login form
with st.form("login_form"):
    st.write("Please login to continue")
    input_username = st.text_input("Username")
    input_password = st.text_input("Password", type="password")
    submit_button = st.form_submit_button("Login")

if submit_button:
    if authenticate(input_username, input_password):
        st.success("Login successful!")
        
        # Data submission section
        st.subheader("Enter New Run Data")
        run_type = st.selectbox("Run Type", ["Endurance", "Stamina", "Speed"])
        distance = st.number_input("Distance (km)", min_value=0.0)
        time = st.number_input("Time (minutes)", min_value=0.0)
        submit_data_button = st.button("Submit Data")
        
        if submit_data_button:
            with connect_to_snowflake() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO run_data (username, run_type, distance, time)
                    VALUES (%s, %s, %s, %s)
                """, (input_username, run_type, distance, time))
                st.success("Data submitted successfully!")
        
        # Data visualization
        st.subheader("Run Analysis")
        with connect_to_snowflake() as conn:
            query = f"SELECT run_type, distance, time FROM run_data WHERE username = '{input_username}'"
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
        st.write("Based on your previous runs, here are some goals:")
        for run in ["Endurance", "Stamina", "Speed"]:
            recent_run = df[df["run_type"] == run].sort_values("distance", ascending=False).head(1)
            if not recent_run.empty:
                goal_distance = recent_run["distance"].values[0] * 1.1  # 10% increase
                goal_time = recent_run["time"].values[0] * 0.9  # 10% decrease in time
                st.write(f"{run} - Goal Distance: {goal_distance:.2f} km, Goal Time: {goal_time:.2f} minutes")
    else:
        st.error("Invalid credentials. Please try again.")
