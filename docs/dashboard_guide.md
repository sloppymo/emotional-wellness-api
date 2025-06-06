# Clinical Dashboard User Guide

## Overview

The Emotional Wellness Clinical Dashboard provides real-time insights into patient mental health trends, intervention effectiveness, and early warning indicators. This guide will help you navigate and utilize all dashboard features effectively.

## Accessing the Dashboard

1. Navigate to `http://localhost:8000/dashboard` (or your deployment URL)
2. Log in with your clinician or admin credentials
3. You'll be redirected to the main dashboard overview

**Note**: Only users with `clinician` or `admin` roles can access the dashboard.

## Dashboard Sections

### 1. Overview Page

The main dashboard page displays:

#### Key Metrics
- **Active Patients**: Total number of patients with recent activity
- **Today's Assessments**: Number of assessments completed today
- **Success Rate**: Overall intervention success rate (last 30 days)
- **Weekly Trend**: Percentage change in crisis events from last week

#### Visual Components
- **Crisis Events Chart**: 7-day trend of crisis events
- **Risk Distribution**: Pie chart showing patient distribution by risk level
- **Early Warning Indicators**: Table of patients requiring immediate attention
- **Recent Activity**: Real-time log of system activity

### 2. Crisis Trends Analysis

Access via: Navigation menu → Crisis Trends

#### Features
- **Temporal Analysis**: View crisis patterns by hour, day, or week
- **Trend Visualization**: Interactive line charts showing crisis event frequency
- **Hotspot Detection**: Identify time periods with elevated crisis activity
- **Predictive Insights**: AI-generated predictions for upcoming periods

#### How to Use
1. Select time period (daily/weekly/monthly) from dropdown
2. Choose date range using the date picker
3. Click "Refresh" to update data
4. Hover over chart points for detailed information

### 3. Risk Stratification

Access via: Navigation menu → Risk Stratification

#### Features
- **Cohort Analysis**: Patients grouped by risk level (High/Moderate/Low)
- **Risk Distribution**: Visual breakdown of patient risk levels
- **Risk Factors**: Top contributing factors to patient risk
- **Recommendations**: AI-generated recommendations for each cohort

#### Actions
- Click on a cohort to view patient list
- Export cohort data using "Export CSV" button
- Schedule bulk interventions for high-risk cohorts

### 4. Wellness Trajectories

Access via: Navigation menu → Wellness Trajectories

#### Features
- **Individual Tracking**: Monitor specific patient wellness over time
- **Cohort Comparison**: Compare trajectories across risk groups
- **Improvement Metrics**: Track wellness score changes
- **Predictive Modeling**: View projected wellness trajectories

#### How to Use
1. Search for a patient using the search bar
2. Select trajectory timeframe (7/30/90 days)
3. Toggle between individual and cohort views
4. Use zoom controls to examine specific periods

### 5. Intervention Outcomes

Access via: Navigation menu → Intervention Outcomes

#### Features
- **Effectiveness Metrics**: Success rates by intervention type
- **Protocol Performance**: Compare different intervention protocols
- **Time to Resolution**: Average time for successful interventions
- **Outcome Distribution**: Breakdown of intervention results

#### Analysis Options
- Filter by protocol type
- Compare time periods
- View detailed protocol statistics
- Export outcome reports

## Real-Time Features

### WebSocket Notifications
The dashboard receives real-time updates for:
- New crisis alerts
- Task completion notifications
- Early warning triggers
- System alerts

### Auto-Refresh
Data automatically refreshes:
- Overview metrics: Every 30 seconds
- Early warnings: Every 60 seconds
- Charts: Every 5 minutes

## Task Management

### Submitting Analysis Tasks

1. Click "Run Analysis" button on any dashboard page
2. Select analysis type:
   - Crisis Trends Analysis
   - Risk Stratification
   - Wellness Trajectory
   - Intervention Outcomes
3. Configure parameters
4. Click "Submit"

### Monitoring Task Progress

- Progress bar shows completion percentage
- Real-time status updates in notification area
- Click task ID for detailed progress
- Cancel running tasks if needed

## Early Warning System

### Understanding Alerts

Alert levels:
- **🔴 Critical**: Immediate intervention required
- **🟡 Warning**: Elevated risk, monitor closely
- **🔵 Info**: Notable changes, routine follow-up

### Alert Actions

For each alert, you can:
1. **View Patient**: Open detailed patient profile
2. **Start Intervention**: Launch intervention protocol
3. **Schedule Follow-up**: Book appointment
4. **Dismiss**: Mark as reviewed (with reason)

## Data Export

### Available Formats
- CSV for spreadsheet analysis
- JSON for data integration
- PDF for reports

### Export Options
1. Click "Export" button on any data view
2. Select format and date range
3. Choose fields to include
4. Click "Download"

## Customization

### Dashboard Preferences

Access via: User menu → Preferences

Customize:
- Default time ranges
- Chart colors and styles
- Auto-refresh intervals
- Notification preferences

### Saved Views

Create custom dashboard views:
1. Configure dashboard as desired
2. Click "Save View"
3. Name your view
4. Access from "Saved Views" dropdown

## Best Practices

### Daily Workflow
1. Check Overview page for alerts
2. Review Early Warning Indicators
3. Analyze Crisis Trends for patterns
4. Update intervention plans as needed

### Weekly Tasks
1. Run Risk Stratification analysis
2. Review cohort wellness trajectories
3. Evaluate intervention effectiveness
4. Export reports for team meetings

### Monthly Reviews
1. Comprehensive outcome analysis
2. Protocol effectiveness comparison
3. System-wide trend analysis
4. Update clinical protocols based on data

## Troubleshooting

### Common Issues

**Dashboard not loading**
- Check internet connection
- Clear browser cache
- Verify login credentials
- Contact IT support

**Data not updating**
- Check auto-refresh is enabled
- Manually refresh page (F5)
- Verify backend services are running

**Export failing**
- Check data range is valid
- Ensure sufficient permissions
- Try smaller date ranges
- Use different format

### Performance Tips
- Use date filters to limit data
- Close unused dashboard tabs
- Enable browser hardware acceleration
- Use modern browsers (Chrome/Firefox/Edge)

## Security & Privacy

### Data Protection
- All data is encrypted in transit
- Role-based access control
- Audit logs for all actions
- HIPAA-compliant design

### Best Practices
- Log out when finished
- Don't share credentials
- Report suspicious activity
- Use secure networks only

## Support

### Getting Help
- In-app help: Click "?" icon
- Documentation: `/docs/dashboard`
- Support email: support@example.com
- Training videos: Available in Help Center

### Feature Requests
Submit suggestions via:
- Feedback button in dashboard
- GitHub issues
- Monthly user meetings

---

**Remember**: The dashboard is a tool to enhance clinical decision-making, not replace it. Always use professional judgment in patient care. 