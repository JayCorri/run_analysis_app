DEV NOTES
Overview
These notes summarize the current state of the project, including Snowflake setup, SMTP configuration, app code status, and a plan for next steps. This file will serve as a reference for seamless resumption of the project.

1. Current Project Status
Snowflake Setup
Database & Schema: Completed setup for the RUN_ANALYSIS_DB database, with the RUN_DATA_SCHEMA schema containing necessary tables.
Warehouse: RUN_ANALYSIS_WH warehouse created and assigned to the app’s user.
Tables Created:
USERS: Stores user information for authentication.
RUN_DATA: Holds the user run data for endurance, stamina, and speed records.
Permissions & Access:
app_user created with limited permissions for security.
Test Data: Verified data insertion and retrieval functionality using app_user credentials.
App Environment Variables (.env)
Snowflake: Variables for Snowflake (account, user, password, database, schema, warehouse) are ready for app integration.
SendGrid (SMTP): Placeholder values added. Actual API key pending after account setup.
SMTP / SendGrid Configuration (In Progress)
Action Needed: Complete setup of SendGrid free account.
Next Steps:
Add API key to .env.
Test email functionality to confirm connection and verify Forgot Password feature.
Streamlit App Code
Current Version: Code includes updated data structure matching Snowflake schema. Next update involves connecting to SendGrid for password recovery.
Testing: Once SendGrid is configured, the password recovery feature can be tested fully within Streamlit.
2. Next Steps
Step 1: Finalize SMTP Configuration with SendGrid
Create SendGrid Account (free tier sufficient).
Update .env with API Key:
plaintext
Copy code
SMTP_SERVER=smtp.sendgrid.net
SMTP_PORT=587
EMAIL_USER=apikey         # Set "apikey" as the user for SendGrid
EMAIL_PASSWORD=<your_sendgrid_api_key_here>  # Replace with actual API key
Test SMTP: Verify functionality with a password recovery email sent to a test account.
Step 2: Git and Version Control
Update Git Repository:
Commit recent updates and include this DEV_NOTES.md for future reference.
Ensure .env file is included in .gitignore to keep credentials secure.
Confirm Repository:
Verify that recent changes are reflected on GitHub, with sensitive data excluded.
Step 3: Final Streamlit App Preparations
Dependencies: Verify requirements.txt includes all necessary packages (e.g., streamlit, snowflake-connector-python, bcrypt).
Deployment Security: Confirm .env or equivalent method secures sensitive data in deployment.
Step 4: Deploy Streamlit App
Streamlit Cloud Setup: Link GitHub repository to Streamlit Cloud.
Deploy App:
Confirm Streamlit Cloud recognizes requirements.txt.
Deploy app and monitor logs for potential errors.
Authorization & Access Configuration (Snowflake)
To ensure proper app functionality, ensure these access details are configured in .env for Snowflake access:

ACCOUNT: Snowflake account identifier.
USER: app_user created specifically for app access.
PASSWORD: Password associated with app_user.
DATABASE: RUN_ANALYSIS_DB
SCHEMA: RUN_DATA_SCHEMA
WAREHOUSE: RUN_ANALYSIS_WH
Test Access (Completed)
Tests were run successfully using app_user, verifying that permissions and access rights align with project requirements.

Code and File Status
App Code: Current version is updated with Snowflake integration. Next step is SMTP/SendGrid configuration.
Break Note: .env placeholder values are prepared; SendGrid setup will be the primary task on resuming.
With these notes, resuming and reviewing the project progress will be straightforward. Let me know if any section requires further detail. Enjoy the break! 😊

PROGRESS 11/4
### DEV NOTES

**Project Overview**
This project is designed to provide personalized run training analysis with Snowflake for data storage and SendGrid for SMTP email recovery functionality.

**Recent Progress**
1. **SMTP (SendGrid) Setup and Testing**:
   - Successfully integrated and tested SendGrid SMTP for password recovery emails.
   - Sender identity verified; emails can now be sent from `run-analysis-app-no-reply@1440maple.com`.

2. **Snowflake Integration**:
   - Snowflake connection verified. User data and run data are successfully stored and retrieved.

3. **Local Testing Strategy**:
   - Created a `/tests` folder with independent local testing scripts for each core functionality.
   - Local tests bypass Streamlit requirements and directly test the functions.
   - Testing scripts are added to `.gitignore` to avoid production conflicts.

**Next Steps**
1. Complete local tests for remaining core functionalities (authentication, data handling).
2. Begin visualizations testing with sample run data.
3. Prepare app for deployment on Streamlit (ensure `requirements.txt` includes all necessary libraries).
4. Streamline deployment configuration on Streamlit Cloud, ensuring `.env.prod` is secure and set up.

**Known Issues & Considerations**
- Local and Streamlit environments conflict during testing. Local tests are isolated in `/tests`, and Streamlit imports are conditionally loaded only when needed.

improve local/deployed flagging clarity by with cleaner code:

Yes, the current TESTING_LOCAL flag setup is functional but can indeed be streamlined to avoid excessive indentation. Here’s a style tweak that maintains the flag's functionality while keeping the indentation minimal for the UI section:

Define a run_ui() function: Enclose all Streamlit code in a run_ui() function and call it conditionally. This avoids the need for an indentation block within the if not TESTING_LOCAL condition.
Simplify Code Structure: This approach keeps the main body uncluttered, and the Streamlit UI only activates in the deployed environment without the need for extra indentation.
Here’s how it would look:

python
Copy code
import os
import pandas as pd
import matplotlib.pyplot as plt
from snowflake.connector import connect
import bcrypt
import smtplib
from email.mime.text import MIMEText

# Check if we’re in local testing mode
TESTING_LOCAL = os.getenv("TESTING_LOCAL", "false").lower() == "true"

# Conditional imports based on environment
if not TESTING_LOCAL:
    import streamlit as st
else:
    from dotenv import load_dotenv
    load_dotenv()  # Load .env variables for local testing

def run_ui():
    """Streamlit UI code, only run when deployed to Streamlit."""
    st.title("Personal Running Analysis")
    # Additional Streamlit code here
    # ...

# Call the UI function only if not in local testing mode
if not TESTING_LOCAL:
    run_ui()
else:
    print("Running in local testing mode. Streamlit UI is bypassed.")
Benefits of This Structure
Reduced Indentation: UI code within run_ui() is clean and maintains default indentation levels.
Modularity: Encapsulating the Streamlit code in run_ui() improves readability and modularity, making the code easier to manage or modify.
Scalability: If additional environment-dependent features arise, you can add other functions with similar condition checks without affecting the main code flow.
This approach keeps the codebase organized and makes switching between local testing and deployment straightforward without excessive indentation.

## Development Notes - Run Analysis Streamlit App

### Date: 2024-11-04

### Version: 1.2 Updates

#### Current Status:
- **Send Recovery Email Function**: 
  - Implemented as a **test-only** feature for now. While the `send_recovery_email` function technically can send emails, it is **non-functional in production** because there is currently no front-end interface for user-initiated password recovery.
  - **Next Steps**: Implement a front-end interface in the app where users can request password resets securely by entering their email or username.

#### Key Changes Since Last Update:
- **Removed Local Testing Flag (`TESTING_LOCAL`)**: 
  - The app now exclusively supports Streamlit Cloud deployment.
  - This simplifies the configuration setup by eliminating the need for separate local `.env` handling, focusing entirely on `st.secrets` for secure production environment variables.
  
- **Consolidated Snowflake & Email Configuration**:
  - Both Snowflake and email configurations are now handled via `st.secrets`, improving deployment security and efficiency by maintaining a single configuration source.
  
- **Version Docstring Expanded**:
  - Updated the code file docstring to provide a detailed summary of current features, limitations, and recent improvements.
  - Includes a note on email recovery functionality status to streamline communication and ensure accurate version tracking.

#### Additional Notes:
- **Functionality Reminder**: The `send_recovery_email` function remains inactive for end-user access until the corresponding front-end interface is built.
- **Future Plans**:
  - Build an end-user interface for password reset.
  - Test email and Snowflake interactions upon Streamlit Cloud deployment.

## User Registration and Password Storage
- Implemented user registration with bcrypt password hashing.
- Updated password storage to use base64 encoding to meet Snowflake VARCHAR storage requirements.
- Authentication now decodes base64-encoded password hashes before bcrypt verification.

### Troubleshooting Notes
- Ensure the Snowflake `users` table `password_hash` column is set to `VARCHAR` type.
- Verify that bcrypt and base64 encoding modules are correctly imported to avoid runtime errors during registration and authentication.

# UX/UI Roadmap
 - After the user logs in they should be presented with the number of miles they've ran over the past week with a navigation bar to change the selector from W M Y All (week, month, year, all). Then their performance goals for next week (we should add they can manually override the performance goals to their preference with a reset button to return to app generated performance goal if that sounds doable). Also, the example data shown at login should have some indication it is an example and disappear after login. The login form should disappear after login and put give them an intial in the top left corner where they can logout bringing them back to the login form with the sample Performance Goal.
After login the user should not be presented with the entire run schedule. Instead the Run Analysis should be the first thing they see, the login and sample performance goal should disappear. The Section Run Analysis should be titled performance goals. and show the three run type scorecards in 1 row, 3 columns. Then beneath is the chart for the week where they can change it W M Y All. Beneath that, at the bottom is the data entry. There should be a menu bar that hovers at the bottom where they can select an icon of a running stick figure to navigate to their performance goals, an icon of a bar chart where they navigate to view their metrics and activity logs, a plus button where they navigate to log a run. I'm not sure how this aligns with our previous UI/UX idea
This UI/UX overhaul aligns well with providing a streamlined, user-friendly experience that centers on actionable insights and accessibility. Here’s a structured breakdown of your new UI/UX vision and how we can implement it within our existing structure, along with some enhancements based on feasibility.

---

### 1. **Login & Sample Data Experience**

   - **Login Form**: Once the user logs in successfully:
     - Hide the login form.
     - Display the user’s initials in the top left, which acts as a logout button to bring them back to the login form. 
     - Display sample performance goals with a label indicating they are sample data until the user logs in.
   - **Sample Data Visibility**: This data will:
     - Disappear once the user logs in.
     - Be replaced by real user performance data and goals.

### 2. **Performance Goals Display**

   - **Initial Display After Login**: Post-login, the user should see a streamlined view that focuses on their performance goals.
     - **Main Performance Goal Metric**: Show cumulative miles over the past week prominently at the top.
     - **Goal Scorecards**:
       - Rename the “Run Analysis” section to “Performance Goals.”
       - Display the three run type scorecards (Endurance, Stamina, Speed) in one row with three columns.
       - Each scorecard provides the weekly performance target and displays progress.
     - **User-Controlled Goal Customization**:
       - Users can manually adjust goals and save them.
       - Provide a “Reset” button to return to the app-generated default goals.

### 3. **Weekly Chart and Time Selector Navigation**

   - **Weekly Chart View**:
     - Place a time selector bar at the top of the chart area, allowing users to toggle between W, M, Y, and All to view their performance data by week, month, year, or all-time.
     - **Chart Display**:
       - Plot the selected time range (weekly, monthly, yearly, or cumulative) as a graph beneath the performance scorecards.
       - This chart provides a quick visual of distance and progress over time.
   
### 4. **Data Entry for Logging Runs**

   - **Data Entry Section**: Position the data entry section for logging new runs at the bottom of the display.
   - **Bottom Navigation Menu**:
     - Introduce a fixed bottom navigation bar with icons to quickly navigate between sections:
       - **Performance Goals**: An icon of a running stick figure to show goals.
       - **Metrics and Activity Logs**: A bar chart icon for detailed metrics and activity logs.
       - **Log Run**: A plus icon for adding new runs.

### 5. **UI Flow Summary**

   - **Upon Login**:
     - Login form disappears, and the user’s initials appear in the top-left corner as a logout option.
     - Sample data clears and is replaced by the user’s actual performance goals and past week’s mileage.
   - **After Login - Main View**:
     - **Top Section**: Weekly mileage, with navigation to switch between W, M, Y, and All views.
     - **Performance Goals Section**: Three scorecards showing weekly goals for Endurance, Stamina, and Speed.
     - **Chart Section**: Time-series chart for selected duration.
     - **Data Entry Section**: At the bottom, with the hover menu for easy navigation.

---

### Implementation Notes

1. **Interactive Chart Navigation**: We’ll implement the time-selector bar and have the data and chart update based on the user’s selection.
2. **User Goal Customization**: Add form fields to allow users to set custom goals, and store these settings for future sessions.
3. **Bottom Navigation**: This floating menu will ensure users can seamlessly switch views without cluttering the main display.
4. **Performance Enhancements**:
   - Streamlining data queries for performance goals and chart metrics based on time selector (W, M, Y, All).
   - Enabling caching of frequent queries (e.g., weekly mileage) for quick load times.
5. **Accessibility & Responsiveness**:
   - The layout will adjust based on screen size (e.g., one row on desktop, cascading rows on mobile).

---

### Next Steps

1. **Mockup Confirmation**: We can develop a quick mockup based on this structure for visual confirmation.
2. **Refactoring Codebase**: Organize the current layout into distinct, modular sections that align with the new UI flow.
3. **Feature Development**: Implement user customization for goals, real-time chart updates, and the bottom navigation bar.

This UI/UX revamp will enhance usability, making key metrics more accessible while keeping navigation intuitive and maintaining mobile-friendliness.