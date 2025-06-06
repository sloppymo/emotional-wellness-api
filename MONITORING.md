# Monitoring, Metrics, and Admin Dashboard Guide

## Overview
This guide details the monitoring, metrics, and admin dashboard features of the Emotional Wellness API. It covers architecture, API usage, UI, extensibility, and operational best practices.

---

## Features
- **Admin Dashboard UI**: Real-time and historical system health, metrics, and alert management
- **RESTful Metrics & Alerts APIs**: Programmatic access for dashboards and automation
- **Historical Metrics Storage**: Redis TimeSeries with multiple aggregation levels
- **Role-based Security**: Only admins can access dashboards and metrics/alerts APIs
- **Advanced Filtering & Export**: Aggregation, label-based, custom date, CSV/JSON export

---

## Architecture & Components
- **Routers**: `dashboard/admin_router.py`, `routers/metrics.py`, `routers/alerts.py`
- **Templates**: `dashboard/templates/admin/`
- **Metrics Storage**: `monitoring/metrics_storage.py`
- **Collector**: `monitoring/metrics_collector.py`

---

## API Reference

### Authentication
All endpoints require an admin JWT:
```
Authorization: Bearer <your_admin_jwt>
```

### Endpoints
- `GET /metrics` — List all metrics
- `GET /metrics/{metric}` — Fetch metric data (time range, aggregation, label filters)
- `DELETE /metrics/{metric}` — Delete a metric
- `GET /alerts` — List and filter alerts
- `POST /alerts/{id}/acknowledge|resolve|silence` — Alert lifecycle actions

See the main API docs or OpenAPI/Swagger for full details.

---

## Admin Dashboard UI

### Pages
- **Dashboard**: Overview, system health, activity
- **Monitoring**: Real-time health, metrics, alerts
- **Alerts**: Filter, manage, act on alerts
- **Metrics**: Historical charts, filters, export
- **Tasks & Integrations**: Background and external system health

### Metrics Dashboard Features
- Dynamic metric selection (populated from `/metrics` API)
- Time range and custom date selection
- Aggregation (raw, hourly, daily, monthly)
- Label-based filtering
- CSV/JSON export
- Live chart/table updates

---

## Extending & Customizing
- **Add new metrics**: Extend `metrics_collector.py` and they appear automatically
- **Custom alerts**: Define new rules in `alert_rules.py`
- **UI**: Edit Jinja2 templates for branding or new pages

---

## Testing & Troubleshooting
- Integration tests: See `tests/integration/test_metrics_dashboard.py`
- Manual: Use the dashboard UI as admin
- Troubleshooting: Check Redis, logs, and JWT validity

---

## Roadmap
- Anomaly detection, trend analysis
- Security event dashboards
- Audit/compliance enhancements

---

For more, see the main README or contact the engineering team.
