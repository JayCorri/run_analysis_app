# Changelog

## Version 2.0 - 2024-11-06

### Added
- **Dynamic Regimen Selection**: Users can now select from multiple training regimens, starting with the "NSW Candidate Run Regimen" and the "Marathon Trainer Regimen." Future regimens can be added easily, enhancing flexibility and personalization.
- **Database-Driven Schedule Storage**: Training regimens are stored in Snowflake, allowing users to switch regimens dynamically. The default regimen is "NSW Candidate Run Regimen."
- **Maintenance Mode**: Automatically prompts users to switch to "Maintenance Mode" once they complete the final week of any regimen, repeating the last week’s schedule if they choose not to advance to a new regimen.
- **Goal Visualization Improvements**: Updated goal tracking display with weekly goals per user-selected regimen, including endurance, stamina, and speed.
- **Marathon Trainer Integration**: Marathon Trainer Regimen includes options for long-distance training with specific intervals and tempos for optimal conditioning.

### Changed
- **UI Overhaul**: Streamlined UI with separate sections for performance analysis, weekly goal tracking, and regimen management. Optimized mobile views with a bottom navigation bar for easy access to main features.
- **Enhanced Goal Tracking and Personalization**: Weekly goals and progress tracking now reflect the selected regimen, dynamically adjusting based on user preferences and schedule progression.
- **Streamlined Data Flow**: Simplified SQL queries for regimen selection and schedule updates to improve performance and maintainability.

### Fixed
- **Error Handling for Regimen Transitions**: Added validation to ensure smooth transition between regimens with appropriate prompts for next steps.
- **Database Integrity Checks**: Enhanced validation for user data to prevent duplicate or missing records when switching regimens.
- **UI Loading Issues on Mobile**: Improved mobile performance by optimizing page load times and data fetching for a responsive experience.
