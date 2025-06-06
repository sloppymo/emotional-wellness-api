from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import json
import asyncio
from dataclasses import dataclass, asdict
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse, JSONResponse
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from redis.asyncio import Redis
import numpy as np
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

@dataclass
class DashboardMetrics:
    """Dashboard metrics data structure."""
    total_requests: int
    rate_limited_requests: int
    unique_clients: int
    top_endpoints: List[Dict[str, Any]]
    geographic_distribution: Dict[str, int]
    error_rate: float
    avg_response_time: float
    circuit_breaker_trips: int
    anomaly_detections: int

class RateLimitDashboard:
    """Dashboard and visualization system for rate limiting metrics."""
    
    def __init__(self, redis_client: Redis, app: FastAPI):
        self.redis = redis_client
        self.app = app
        self.setup_routes()
    
    def setup_routes(self):
        """Setup dashboard routes."""
        
        @self.app.get("/rate-limit/dashboard", response_class=HTMLResponse)
        async def dashboard():
            """Main dashboard page."""
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Rate Limit Dashboard</title>
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
                <style>
                    body { font-family: Arial, sans-serif; margin: 0; padding: 20px; }
                    .metric-card { 
                        background: #f5f5f5; 
                        padding: 20px; 
                        margin: 10px; 
                        border-radius: 8px;
                        display: inline-block;
                        min-width: 200px;
                    }
                    .metric-value { font-size: 2em; color: #2c3e50; }
                    .metric-label { color: #7f8c8d; }
                    .chart-container { width: 100%; height: 400px; margin: 20px 0; }
                </style>
            </head>
            <body>
                <h1>Rate Limit Dashboard</h1>
                
                <div id="metrics-cards"></div>
                
                <div class="chart-container">
                    <div id="requests-chart"></div>
                </div>
                
                <div class="chart-container">
                    <div id="geographic-chart"></div>
                </div>
                
                <div class="chart-container">
                    <div id="endpoints-chart"></div>
                </div>
                
                <script>
                    async function loadDashboard() {
                        // Load metrics
                        const metricsResponse = await fetch('/rate-limit/api/metrics');
                        const metrics = await metricsResponse.json();
                        
                        // Update metric cards
                        updateMetricCards(metrics);
                        
                        // Load and render charts
                        await renderRequestsChart();
                        await renderGeographicChart();
                        await renderEndpointsChart();
                    }
                    
                    function updateMetricCards(metrics) {
                        const cardsHtml = `
                            <div class="metric-card">
                                <div class="metric-value">${metrics.total_requests.toLocaleString()}</div>
                                <div class="metric-label">Total Requests</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">${metrics.rate_limited_requests.toLocaleString()}</div>
                                <div class="metric-label">Rate Limited</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">${metrics.unique_clients.toLocaleString()}</div>
                                <div class="metric-label">Unique Clients</div>
                            </div>
                            <div class="metric-card">
                                <div class="metric-value">${(metrics.error_rate * 100).toFixed(2)}%</div>
                                <div class="metric-label">Error Rate</div>
                            </div>
                        `;
                        document.getElementById('metrics-cards').innerHTML = cardsHtml;
                    }
                    
                    async function renderRequestsChart() {
                        const response = await fetch('/rate-limit/api/requests-timeline');
                        const data = await response.json();
                        
                        const trace = {
                            x: data.timestamps,
                            y: data.request_counts,
                            type: 'scatter',
                            mode: 'lines+markers',
                            name: 'Requests per minute'
                        };
                        
                        const layout = {
                            title: 'Requests Timeline',
                            xaxis: { title: 'Time' },
                            yaxis: { title: 'Requests' }
                        };
                        
                        Plotly.newPlot('requests-chart', [trace], layout);
                    }
                    
                    async function renderGeographicChart() {
                        const response = await fetch('/rate-limit/api/geographic-distribution');
                        const data = await response.json();
                        
                        const trace = {
                            type: 'choropleth',
                            locations: data.countries,
                            z: data.request_counts,
                            colorscale: 'Blues'
                        };
                        
                        const layout = {
                            title: 'Geographic Distribution',
                            geo: { showframe: false, showcoastlines: false }
                        };
                        
                        Plotly.newPlot('geographic-chart', [trace], layout);
                    }
                    
                    async function renderEndpointsChart() {
                        const response = await fetch('/rate-limit/api/top-endpoints');
                        const data = await response.json();
                        
                        const trace = {
                            x: data.endpoints,
                            y: data.request_counts,
                            type: 'bar'
                        };
                        
                        const layout = {
                            title: 'Top Endpoints by Request Count',
                            xaxis: { title: 'Endpoints' },
                            yaxis: { title: 'Requests' }
                        };
                        
                        Plotly.newPlot('endpoints-chart', [trace], layout);
                    }
                    
                    // Load dashboard on page load
                    loadDashboard();
                    
                    // Refresh every 30 seconds
                    setInterval(loadDashboard, 30000);
                </script>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
        
        @self.app.get("/rate-limit/api/metrics")
        async def get_metrics():
            """Get dashboard metrics."""
            metrics = await self.get_dashboard_metrics()
            return JSONResponse(content=asdict(metrics))
        
        @self.app.get("/rate-limit/api/requests-timeline")
        async def get_requests_timeline():
            """Get requests timeline data."""
            return await self.get_requests_timeline()
        
        @self.app.get("/rate-limit/api/geographic-distribution")
        async def get_geographic_distribution():
            """Get geographic distribution data."""
            return await self.get_geographic_distribution()
        
        @self.app.get("/rate-limit/api/top-endpoints")
        async def get_top_endpoints():
            """Get top endpoints data."""
            return await self.get_top_endpoints()
        
        @self.app.get("/rate-limit/prometheus")
        async def prometheus_metrics():
            """Prometheus metrics endpoint."""
            return Response(
                content=generate_latest(),
                media_type=CONTENT_TYPE_LATEST
            )
    
    async def get_dashboard_metrics(self) -> DashboardMetrics:
        """Get aggregated dashboard metrics."""
        # Get metrics from Redis
        total_requests = int(await self.redis.get("metrics:total_requests") or 0)
        rate_limited = int(await self.redis.get("metrics:rate_limited") or 0)
        unique_clients = await self.redis.scard("metrics:unique_clients") or 0
        circuit_breaker_trips = int(await self.redis.get("metrics:circuit_breaker_trips") or 0)
        anomaly_detections = int(await self.redis.get("metrics:anomaly_detections") or 0)
        
        # Calculate error rate
        error_rate = rate_limited / total_requests if total_requests > 0 else 0
        
        # Get top endpoints
        top_endpoints_data = await self.redis.zrevrange("metrics:endpoints", 0, 9, withscores=True)
        top_endpoints = [
            {"endpoint": endpoint.decode(), "count": int(count)}
            for endpoint, count in top_endpoints_data
        ]
        
        # Get geographic distribution
        geo_data = await self.redis.hgetall("metrics:geographic")
        geographic_distribution = {
            country.decode(): int(count)
            for country, count in geo_data.items()
        }
        
        # Get average response time
        avg_response_time = float(await self.redis.get("metrics:avg_response_time") or 0)
        
        return DashboardMetrics(
            total_requests=total_requests,
            rate_limited_requests=rate_limited,
            unique_clients=unique_clients,
            top_endpoints=top_endpoints,
            geographic_distribution=geographic_distribution,
            error_rate=error_rate,
            avg_response_time=avg_response_time,
            circuit_breaker_trips=circuit_breaker_trips,
            anomaly_detections=anomaly_detections
        )
    
    async def get_requests_timeline(self) -> Dict[str, List]:
        """Get requests timeline for the last 24 hours."""
        now = datetime.now()
        timestamps = []
        request_counts = []
        
        for i in range(144):  # 24 hours in 10-minute intervals
            timestamp = now - timedelta(minutes=i * 10)
            key = f"metrics:timeline:{timestamp.strftime('%Y%m%d%H%M')}"
            count = int(await self.redis.get(key) or 0)
            
            timestamps.append(timestamp.isoformat())
            request_counts.append(count)
        
        return {
            "timestamps": list(reversed(timestamps)),
            "request_counts": list(reversed(request_counts))
        }
    
    async def get_geographic_distribution(self) -> Dict[str, List]:
        """Get geographic distribution data."""
        geo_data = await self.redis.hgetall("metrics:geographic")
        
        countries = []
        request_counts = []
        
        for country, count in geo_data.items():
            countries.append(country.decode())
            request_counts.append(int(count))
        
        return {
            "countries": countries,
            "request_counts": request_counts
        }
    
    async def get_top_endpoints(self) -> Dict[str, List]:
        """Get top endpoints data."""
        top_endpoints_data = await self.redis.zrevrange("metrics:endpoints", 0, 19, withscores=True)
        
        endpoints = []
        request_counts = []
        
        for endpoint, count in top_endpoints_data:
            endpoints.append(endpoint.decode())
            request_counts.append(int(count))
        
        return {
            "endpoints": endpoints,
            "request_counts": request_counts
        }
    
    async def update_metrics(
        self,
        endpoint: str,
        client_id: str,
        country: str,
        is_rate_limited: bool,
        response_time: float
    ):
        """Update dashboard metrics."""
        # Update total requests
        await self.redis.incr("metrics:total_requests")
        
        # Update rate limited requests
        if is_rate_limited:
            await self.redis.incr("metrics:rate_limited")
        
        # Update unique clients
        await self.redis.sadd("metrics:unique_clients", client_id)
        
        # Update endpoint counts
        await self.redis.zincrby("metrics:endpoints", 1, endpoint)
        
        # Update geographic distribution
        await self.redis.hincrby("metrics:geographic", country, 1)
        
        # Update timeline
        now = datetime.now()
        timeline_key = f"metrics:timeline:{now.strftime('%Y%m%d%H%M')}"
        await self.redis.incr(timeline_key)
        await self.redis.expire(timeline_key, 86400)  # Expire after 24 hours
        
        # Update average response time
        current_avg = float(await self.redis.get("metrics:avg_response_time") or 0)
        total_requests = int(await self.redis.get("metrics:total_requests") or 1)
        new_avg = (current_avg * (total_requests - 1) + response_time) / total_requests
        await self.redis.set("metrics:avg_response_time", str(new_avg))
        
        # Clean up old data
        await self._cleanup_old_metrics()
    
    async def _cleanup_old_metrics(self):
        """Clean up old metrics data."""
        # Clean up old timeline data (keep only last 24 hours)
        cutoff = datetime.now() - timedelta(hours=24)
        cutoff_key = f"metrics:timeline:{cutoff.strftime('%Y%m%d%H%M')}"
        
        # This is a simplified cleanup - in production you'd want more sophisticated cleanup
        pass
    
    async def generate_report(
        self,
        start_date: datetime,
        end_date: datetime,
        format: str = "json"
    ) -> Dict[str, Any]:
        """Generate a comprehensive rate limiting report."""
        metrics = await self.get_dashboard_metrics()
        timeline = await self.get_requests_timeline()
        
        report = {
            "report_period": {
                "start": start_date.isoformat(),
                "end": end_date.isoformat()
            },
            "summary": asdict(metrics),
            "timeline": timeline,
            "geographic_distribution": await self.get_geographic_distribution(),
            "top_endpoints": await self.get_top_endpoints(),
            "generated_at": datetime.now().isoformat()
        }
        
        if format == "html":
            return await self._generate_html_report(report)
        
        return report
    
    async def _generate_html_report(self, report_data: Dict[str, Any]) -> str:
        """Generate HTML report."""
        html_template = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Rate Limiting Report</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 40px; }
                .header { border-bottom: 2px solid #2c3e50; padding-bottom: 20px; }
                .metric { background: #f8f9fa; padding: 15px; margin: 10px 0; border-left: 4px solid #3498db; }
                .metric-value { font-size: 1.5em; font-weight: bold; color: #2c3e50; }
                .section { margin: 30px 0; }
                table { width: 100%; border-collapse: collapse; }
                th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f2f2f2; }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Rate Limiting Report</h1>
                <p>Period: {{ report_period.start }} to {{ report_period.end }}</p>
                <p>Generated: {{ generated_at }}</p>
            </div>
            
            <div class="section">
                <h2>Summary Metrics</h2>
                <div class="metric">
                    <div class="metric-value">{{ summary.total_requests }}</div>
                    <div>Total Requests</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ summary.rate_limited_requests }}</div>
                    <div>Rate Limited Requests</div>
                </div>
                <div class="metric">
                    <div class="metric-value">{{ summary.unique_clients }}</div>
                    <div>Unique Clients</div>
                </div>
            </div>
            
            <div class="section">
                <h2>Top Endpoints</h2>
                <table>
                    <tr><th>Endpoint</th><th>Request Count</th></tr>
                    {% for endpoint in top_endpoints.endpoints[:10] %}
                    <tr>
                        <td>{{ endpoint }}</td>
                        <td>{{ top_endpoints.request_counts[loop.index0] }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </body>
        </html>
        """
        
        from jinja2 import Template
        template = Template(html_template)
        return template.render(**report_data) 