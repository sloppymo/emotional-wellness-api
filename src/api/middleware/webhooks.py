from typing import Dict, Optional
import asyncio
import httpx
import json
import logging
from redis.asyncio import Redis

class WebhookAlert:
    def __init__(self, redis_client: Redis):
        self.redis = redis_client
        self.logger = logging.getLogger(__name__)
        self.http_client = httpx.AsyncClient()
    
    async def send_alert(self, webhook_url: str, message: str):
        """Send webhook alert."""
        try:
            payload = {"text": message}
            response = await self.http_client.post(
                webhook_url,
                json=payload
            )
            response.raise_for_status()
            self.logger.info(f"Alert sent to {webhook_url}")
        except Exception as e:
            self.logger.error(f"Failed to send alert: {e}")
    
    async def cleanup(self):
        """Cleanup resources."""
        await self.http_client.aclose() 