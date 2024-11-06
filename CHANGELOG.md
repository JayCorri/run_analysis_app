# Changelog

## Version 1.3 - 2024-11-06

### Added
- **UI Enhancements**: Scorecards for endurance, stamina, and speed goals are now displayed in a color-coded, mobile-friendly format.
- **Default Weekly Goals**: New users now see default beginner goals derived from the `schedule_df` data, providing metrics like distance, pace, and time to help with initial setup.
- **Modular SQL Queries**: Implemented flexible, predefined SQL queries with SQLAlchemy for improved data retrieval, ensuring modularity and scalability across the app.
- **Goal Overrides**: Users can now manually adjust their performance goals and reset to system-generated defaults as desired.
- **Rep-based Data Handling**: Enhanced `run_data` table structure to support reps for both stamina and speed runs, allowing detailed tracking of repetitions, distance, and time.
- **Sample Schedule for Login Page**: Displays a sample schedule prior to login, which resets upon user authentication.

### Changed
- **SQLAlchemy Integration**: Transitioned from direct Snowflake connection to SQLAlchemy, utilizing a `get_engine()` function for all database connections and optimized for maintainability.
- **Data Entry and Goal Tracking**: Revised data entry forms to use the updated `schedule_df` structure, pulling goals dynamically for each week.
- **UI Flow**: Improved UI flow to display only relevant sections based on login status; login and sample data now disappear upon authentication.
- **Mobile-First Design**: Revised layout to support cascading scorecards on mobile with bottom navigation icons for performance goals, metrics, and data entry.

### Fixed
- **Error Handling**: Added error handling for cases where no user data is present, defaulting to Week 1 beginner goals for new users.
- **Data Type Conflicts**: Addressed data type issues in `run_data` fields, ensuring `rep_distance` and `rep_time` are stored as floats for accurate tracking.
- **Syntax Corrections**: Resolved SQL syntax errors in queries with `%s` placeholders, converting to SQLAlchemy-compatible syntax.
- **Missing Goal Data**: Implemented checks to ensure user-specific or default goals are always displayed.

## Version 1.2
- **User Registration**: Users can now create accounts directly from the app.
- **Secure Password Storage**: Passwords are hashed and stored using base64 encoding, ensuring compatibility with Snowflake's VARCHAR type.
- **Enhanced Authentication**: Decodes passwords from base64 to verify credentials securely.
