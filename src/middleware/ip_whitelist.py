"""
IP Whitelisting Middleware for Administrative Routes
Allows requests only from approved IP addresses for administrative operations.
"""
import ipaddress
from typing import List, Optional, Callable
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

from core.config import settings
import structured_logging.structured as log

class IPWhitelistMiddleware(BaseHTTPMiddleware):
    """
    Middleware that checks if the client IP is in the whitelist for admin routes.
    
    Only applies the check to routes that match the defined admin route patterns.
    """
    def __init__(
        self, 
        app, 
        whitelist: Optional[List[str]] = None,
        admin_routes: Optional[List[str]] = None
    ):
        super().__init__(app)
        # Use provided whitelist or load from settings
        self.whitelist = whitelist or settings.ADMIN_IP_WHITELIST
        self.admin_routes = admin_routes or settings.ADMIN_ROUTE_PATTERNS
        self.networks = []
        
        # Convert IP strings to network objects for easy checking
        for ip in self.whitelist:
            try:
                # Handle both single IPs and CIDR notation
                if "/" in ip:
                    self.networks.append(ipaddress.ip_network(ip, strict=False))
                else:
                    self.networks.append(ipaddress.ip_address(ip))
            except ValueError:
                log.error(f"Invalid IP or CIDR in whitelist: {ip}", extra={"ip": ip})
    
    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Only apply to admin routes
        if self._is_admin_route(request.url.path):
            client_ip = self._get_client_ip(request)
            if not self._is_ip_allowed(client_ip):
                log.warning(
                    "IP whitelist restriction: Access denied",
                    extra={
                        "ip": client_ip,
                        "path": request.url.path,
                        "method": request.method
                    }
                )
                raise HTTPException(
                    status_code=403,
                    detail="Access denied based on IP restriction"
                )
            
            # Log successful admin access
            log.info(
                "Administrative route accessed", 
                extra={
                    "ip": client_ip,
                    "path": request.url.path,
                    "method": request.method
                }
            )
            
        return await call_next(request)
    
    def _is_admin_route(self, path: str) -> bool:
        """Check if the path matches any admin route pattern."""
        return any(admin_pattern in path for admin_pattern in self.admin_routes)
    
    def _get_client_ip(self, request: Request) -> str:
        """Extract client IP address from request."""
        # Check for X-Forwarded-For header (when behind proxy/load balancer)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            # Get the original client IP (first in the chain)
            return forwarded_for.split(",")[0].strip()
        
        # Fallback to direct client address
        # In FastAPI/Starlette, client and scope["client"] contain (host, port) tuple
        return request.client.host if request.client else "unknown"
    
    def _is_ip_allowed(self, client_ip: str) -> bool:
        """Check if the IP is in the allowed list."""
        if not client_ip or client_ip == "unknown":
            return False
            
        try:
            ip_obj = ipaddress.ip_address(client_ip)
            
            # Check if IP is in any of our allowed networks
            for network in self.networks:
                if isinstance(network, ipaddress.IPv4Network) or isinstance(network, ipaddress.IPv6Network):
                    if ip_obj in network:
                        return True
                elif network == ip_obj:
                    return True
                    
            return False
        except ValueError:
            log.error(f"Invalid client IP format: {client_ip}", extra={"ip": client_ip})
            return False
