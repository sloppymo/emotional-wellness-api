from typing import Dict, Any
from datetime import datetime
from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse
from redis.asyncio import Redis

class RateLimitDashboard:
    """Simple dashboard for rate limiting metrics."""
    
    def __init__(self, redis_client: Redis, app: FastAPI):
        self.redis = redis_client
        self.app = app
        self.setup_routes()
    
    def setup_routes(self):
        """Setup dashboard routes."""
        
        @self.app.get("/dashboard", response_class=HTMLResponse)
        async def dashboard():
            """Main dashboard page."""
            html_content = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Rate Limit Dashboard</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 20px; }
                    .metric { background: #f5f5f5; padding: 20px; margin: 10px; border-radius: 8px; }
                </style>
            </head>
            <body>
                <h1>Rate Limit Dashboard</h1>
                <div id="metrics"></div>
                <script>
                    async function loadMetrics() {
                        const response = await fetch('/metrics');
                        const data = await response.json();
                        document.getElementById('metrics').innerHTML = 
                            '<div class="metric">Total Requests: ' + data.total_requests + '</div>' +
                            '<div class="metric">Rate Limited: ' + data.rate_limited + '</div>';
                    }
                    loadMetrics();
                </script>
            </body>
            </html>
            """
            return HTMLResponse(content=html_content)
        
        @self.app.get("/metrics")
        async def get_metrics():
            """Get basic metrics."""
            total_requests = int(await self.redis.get("metrics:total_requests") or 0)
            rate_limited = int(await self.redis.get("metrics:rate_limited") or 0)
            
            return JSONResponse(content={
                "total_requests": total_requests,
                "rate_limited": rate_limited,
                "timestamp": datetime.now().isoformat()
            })
    
    async def update_metrics(self, is_rate_limited: bool):
        """Update metrics."""
        await self.redis.incr("metrics:total_requests")
        if is_rate_limited:
            await self.redis.incr("metrics:rate_limited") 