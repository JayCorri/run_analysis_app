# Changelog

## v3.1.1 - Error Handling and Logging Enhancements - 2024-11-07

### Added
- **Error Handling**: Added robust error handling across all backend functions, with each function wrapped in a logging mechanism to capture errors.

### Changed
- **Error Logging to Database**: Errors are now logged to a dedicated database table (`error_logs`), storing details like timestamp, function name, error message, and relevant parameters.
- **Error Notification in Streamlit**: Each error triggers a user-friendly message within the Streamlit app, providing immediate feedback about where the issue occurred.

### Fixed
- **Improved Code Structure**: Streamlined backend functions with consistent error logging practices, enhancing reliability and debugging efficiency.

## v3.1 - Major Structural Update - 2024-11-07

### Added
- **New Regimen Selection**: Users can now choose between multiple training regimens.
- **Session Persistence**: Users' regimen and current week settings are saved across sessions.
- **Run Analysis with Metrics**: Tracks and displays data for endurance, stamina, and speed runs.

### Changed
- **Modular Structure**: Separated backend logic to `run_analysis_backend.py` and UI code to `run_analysis_streamlit_app.py` for maintainability and scalability.
- **Database**: Integrated Snowflake as the primary data store for all user and run data.
- **Error Handling**: Enhanced error handling in database operations with more descriptive feedback in Streamlit.

## v3.0 - Major Enhancements and Database Restructure - 2024-11-06

### Added
- **Session Persistence**: User-selected regimen and week settings are now persistent across sessions.
- **Dynamic Week Progression**: System increments weekly training schedules based on user performance and goals.
- **Custom Regimen Logic**: NSW regimen defaults to maintenance mode after week 34. Marathon regimen handles specialized weeks (marathon and short/fast weeks).
- **Error Handling Improvements**: Enhanced error handling and logging for a more resilient user experience.

### Changed
- **Database Consolidation**: All schedules now stored in Snowflake with revised `schedules` table, eliminating the `schedule_df` dataframe dependency.
- **User Table Structure**: Modified `users` table to track regimen preferences, allowing week progressions to persist across sessions.
- **Code Refactoring**: Refactored functions to integrate Snowflake queries, streamline goal checks, and remove deprecated schedule dataframes.

### Fixed
- Fixed various session management issues causing users to be logged out on certain UI changes.
- Addressed `regimen_id` and other parameter binding issues across Snowflake SQL queries.

## Version 2.1 - 2024-11-06

### Added
- **Dynamic Regimen Selection**: Users can now select from multiple training regimens, starting with the "NSW Candidate Run Regimen" and the "Marathon Trainer Regimen." Future regimens can be added easily, enhancing flexibility and personalization.
- **Database-Driven Schedule Storage**: Training regimens are stored in Snowflake, allowing users to switch regimens dynamically. The default regimen is "NSW Candidate Run Regimen."
- **Maintenance Mode**: Automatically prompts users to switch to "Maintenance Mode" once they complete the final week of any regimen, repeating the last week’s schedule if they choose not to advance to a new regimen.
- **Goal Visualization Improvements**: Updated goal tracking display with weekly goals per user-selected regimen, including endurance, stamina, and speed.
- **Marathon Trainer Integration**: Marathon Trainer Regimen includes options for long-distance training with specific intervals and tempos for optimal conditioning.
- **Unified Training Regimens Table**: Combined all training schedules (NSW Candidate Regimen and Marathon Trainer Regimen) into a single `SCHEDULES` table.
- **Regimen Selection in UI**: Users can now select a regimen from available options, defaulting to the NSW Candidate Regimen.
- **Enhanced Database Structure for Multiple Regimens**: Streamlined database schema by adding a `regimen_id` foreign key in `SCHEDULES`, referencing `TRAINING_REGIMENS` for easier management and scalability of new training regimens.

### Changed
- **UI Overhaul**: Streamlined UI with separate sections for performance analysis, weekly goal tracking, and regimen management. Optimized mobile views with a bottom navigation bar for easy access to main features.
- **Enhanced Goal Tracking and Personalization**: Weekly goals and progress tracking now reflect the selected regimen, dynamically adjusting based on user preferences and schedule progression.
- **Streamlined Data Flow**: Simplified SQL queries for regimen selection and schedule updates to improve performance and maintainability.
- **Database Schema Optimization**: Removed separate tables for NSW Candidate Regimen and Marathon Trainer Regimen, consolidating all schedules into a single `SCHEDULES` table identified by `regimen_id`.
- **Streamlined Regimen Queries**: Updated SQL queries in the app to support unified access to schedules by regimen, allowing seamless addition of future regimens without schema changes.

### Fixed
- **Error Handling for Regimen Transitions**: Added validation to ensure smooth transition between regimens with appropriate prompts for next steps.
- **Database Integrity Checks**: Enhanced validation for user data to prevent duplicate or missing records when switching regimens.
- **UI Loading Issues on Mobile**: Improved mobile performance by optimizing page load times and data fetching for a responsive experience.
- **Error Handling for Missing Schedule Data**: Resolved issues with accessing schedules by ensuring each regimen has a unique `regimen_id`, allowing clear differentiation between regimens.
