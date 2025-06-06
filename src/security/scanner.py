"""
Security scanner module for the Emotional Wellness API.

Provides automatic security scanning capabilities to detect potential
vulnerabilities and security misconfigurations in the application.
"""

import os
import logging
import re
from typing import Dict, List, Set, Optional, Any
import asyncio
from datetime import datetime, timedelta
import json

from fastapi import FastAPI
from redis.asyncio import Redis
import jwt

from structured_logging import get_logger
from observability import get_telemetry_manager, ComponentName, record_span
from config.settings import get_settings


# Configure logger
logger = get_logger(__name__)


class VulnerabilityLevel:
    """Enumeration of vulnerability severity levels."""
    
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SecurityFinding:
    """Represents a security finding from a scan."""
    
    def __init__(
        self,
        title: str,
        description: str,
        level: str,
        component: str,
        recommendation: str,
        timestamp: datetime = None
    ):
        """
        Initialize a security finding.
        
        Args:
            title: Brief title of the finding
            description: Detailed description
            level: Severity level (from VulnerabilityLevel)
            component: The component or area where the finding was detected
            recommendation: Recommended remediation steps
            timestamp: When the finding was detected
        """
        self.title = title
        self.description = description
        self.level = level
        self.component = component
        self.recommendation = recommendation
        self.timestamp = timestamp or datetime.utcnow()
        self.id = f"{component}-{int(self.timestamp.timestamp())}"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary representation."""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "level": self.level,
            "component": self.component,
            "recommendation": self.recommendation,
            "timestamp": self.timestamp.isoformat()
        }


class SecurityScanner:
    """
    Security scanner for detecting vulnerabilities and misconfigurations.
    
    Performs automated security checks and provides recommendations
    for HIPAA-compliant security hardening.
    """
    
    def __init__(self, app: FastAPI, redis: Redis):
        """
        Initialize the security scanner.
        
        Args:
            app: The FastAPI application
            redis: Redis client for storing scan results
        """
        self.app = app
        self.redis = redis
        self._logger = get_logger(f"{__name__}.SecurityScanner")
        self.settings = get_settings()
    
    @record_span("security.scan_environment", ComponentName.SECURITY)
    async def scan_environment(self) -> List[SecurityFinding]:
        """
        Scan environment variables for security issues.
        
        Returns:
            List of security findings
        """
        findings = []
        
        # Check JWT secret strength
        jwt_secret = os.environ.get("JWT_SECRET", "")
        if not jwt_secret or len(jwt_secret) < 32:
            findings.append(SecurityFinding(
                title="Weak JWT Secret",
                description="The JWT secret key is either missing or too short.",
                level=VulnerabilityLevel.CRITICAL,
                component="authentication",
                recommendation="Set a strong JWT_SECRET environment variable with at least 32 random characters."
            ))
        
        # Check CORS settings
        allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*")
        if allowed_origins == "*":
            findings.append(SecurityFinding(
                title="Permissive CORS Policy",
                description="CORS is configured to allow requests from any origin.",
                level=VulnerabilityLevel.HIGH,
                component="middleware",
                recommendation="Restrict ALLOWED_ORIGINS to specific domains required by your application."
            ))
        
        # Check if running in debug mode
        if os.environ.get("DEBUG", "false").lower() == "true":
            findings.append(SecurityFinding(
                title="Debug Mode Enabled",
                description="Application is running in debug mode in a production environment.",
                level=VulnerabilityLevel.MEDIUM,
                component="configuration",
                recommendation="Disable DEBUG mode in production environments."
            ))
        
        # Check rate limiting settings
        rate_limit = int(os.environ.get("RATE_LIMIT_AUTHENTICATED", "100"))
        if rate_limit > 100:
            findings.append(SecurityFinding(
                title="High Rate Limits",
                description=f"Rate limit for authenticated users is set to {rate_limit}, which may be too high.",
                level=VulnerabilityLevel.LOW,
                component="rate_limiting",
                recommendation="Consider lowering the rate limit to prevent abuse."
            ))
        
        # Check Redis security
        redis_url = os.environ.get("REDIS_URL", "")
        if "redis://" in redis_url and "@" not in redis_url:
            findings.append(SecurityFinding(
                title="Unauthenticated Redis Connection",
                description="Redis connection URL does not contain authentication credentials.",
                level=VulnerabilityLevel.HIGH,
                component="data_store",
                recommendation="Configure Redis with authentication and update the REDIS_URL."
            ))
        
        # Log findings
        for finding in findings:
            self._logger.warning(f"Security finding: {finding.title} ({finding.level})")
        
        # Save findings to Redis with 30-day expiration
        if findings:
            scan_id = f"security:scan:{datetime.utcnow().isoformat()}"
            await self.redis.set(
                scan_id,
                json.dumps([f.to_dict() for f in findings]),
                ex=60*60*24*30  # 30 days
            )
            
            # Add to scan history index
            await self.redis.lpush("security:scans", scan_id)
            await self.redis.ltrim("security:scans", 0, 99)  # Keep last 100 scans
        
        return findings
    
    @record_span("security.scan_api_endpoints", ComponentName.SECURITY)
    async def scan_api_endpoints(self) -> List[SecurityFinding]:
        """
        Scan API endpoints for security issues.
        
        Returns:
            List of security findings
        """
        findings = []
        routes = self.app.routes
        
        # Check for routes without authentication
        public_routes = set()
        admin_routes = set()
        
        for route in routes:
            path = getattr(route, "path", "")
            
            # Skip built-in endpoints
            if path in ("/", "/docs", "/redoc", "/openapi.json"):
                continue
                
            # Check for routes that should be protected
            dependencies = getattr(route, "dependencies", [])
            
            # Detect admin routes
            if any(pattern in path for pattern in self.settings.ADMIN_ROUTE_PATTERNS):
                admin_routes.add(path)
            
            # Check if route is protected by authentication
            has_auth = False
            for dep in dependencies:
                if "get_current_user" in str(dep) or "get_api_key" in str(dep):
                    has_auth = True
                    break
            
            if not has_auth and not path.startswith(("/health", "/auth")):
                public_routes.add(path)
        
        # Report public routes that should be authenticated
        if public_routes:
            routes_str = ", ".join(public_routes)
            findings.append(SecurityFinding(
                title="Unauthenticated API Endpoints",
                description=f"The following API endpoints are not protected by authentication: {routes_str}",
                level=VulnerabilityLevel.HIGH,
                component="api_security",
                recommendation="Add authentication dependencies to these routes."
            ))
        
        # Verify admin routes have IP whitelist protection
        for route in admin_routes:
            if not any(re.match(pattern, route) for pattern in self.settings.ADMIN_ROUTE_PATTERNS):
                findings.append(SecurityFinding(
                    title="Administrative Route Without IP Restriction",
                    description=f"Admin route {route} is not protected by IP whitelist.",
                    level=VulnerabilityLevel.MEDIUM,
                    component="api_security",
                    recommendation="Add the route pattern to ADMIN_ROUTE_PATTERNS for IP whitelist protection."
                ))
        
        # Log findings
        for finding in findings:
            self._logger.warning(f"Security finding: {finding.title} ({finding.level})")
        
        return findings
    
    @record_span("security.scan_jwt_configuration", ComponentName.SECURITY)
    async def scan_jwt_configuration(self) -> List[SecurityFinding]:
        """
        Scan JWT configuration for security issues.
        
        Returns:
            List of security findings
        """
        findings = []
        
        # Check JWT algorithm
        jwt_algorithm = os.environ.get("JWT_ALGORITHM", "HS256")
        if jwt_algorithm != "HS256" and jwt_algorithm != "RS256":
            findings.append(SecurityFinding(
                title="Insecure JWT Algorithm",
                description=f"JWT_ALGORITHM is set to {jwt_algorithm}, which may not be secure.",
                level=VulnerabilityLevel.HIGH,
                component="authentication",
                recommendation="Use HS256 or RS256 for JWT signing."
            ))
        
        # Check JWT expiration
        jwt_expiration = int(os.environ.get("JWT_EXPIRATION_MINUTES", "60"))
        if jwt_expiration > 60:
            findings.append(SecurityFinding(
                title="Long JWT Expiration",
                description=f"JWT tokens expire after {jwt_expiration} minutes, which may be too long.",
                level=VulnerabilityLevel.MEDIUM,
                component="authentication",
                recommendation="Reduce JWT_EXPIRATION_MINUTES to 60 minutes or less."
            ))
        
        # Try to create and decode a test token to verify configuration
        try:
            secret = os.environ.get("JWT_SECRET", "test-secret")
            payload = {"sub": "test", "exp": datetime.utcnow() + timedelta(minutes=1)}
            token = jwt.encode(payload, secret, algorithm=jwt_algorithm)
            decoded = jwt.decode(token, secret, algorithms=[jwt_algorithm])
            
            if decoded["sub"] != "test":
                findings.append(SecurityFinding(
                    title="JWT Verification Failure",
                    description="JWT encoding and decoding test failed.",
                    level=VulnerabilityLevel.CRITICAL,
                    component="authentication",
                    recommendation="Check JWT_SECRET and JWT_ALGORITHM configuration."
                ))
        except Exception as e:
            findings.append(SecurityFinding(
                title="JWT Configuration Error",
                description=f"Error testing JWT configuration: {str(e)}",
                level=VulnerabilityLevel.CRITICAL,
                component="authentication",
                recommendation="Verify JWT_SECRET and JWT_ALGORITHM settings."
            ))
        
        # Log findings
        for finding in findings:
            self._logger.warning(f"Security finding: {finding.title} ({finding.level})")
        
        return findings
    
    @record_span("security.full_scan", ComponentName.SECURITY)
    async def full_scan(self) -> Dict[str, Any]:
        """
        Perform a full security scan of the application.
        
        Returns:
            Dictionary with scan results
        """
        # Get current time for performance tracking
        start_time = datetime.utcnow()
        
        # Run all scan types in parallel
        env_findings, api_findings, jwt_findings = await asyncio.gather(
            self.scan_environment(),
            self.scan_api_endpoints(),
            self.scan_jwt_configuration()
        )
        
        # Combine findings
        all_findings = env_findings + api_findings + jwt_findings
        
        # Group by severity
        findings_by_severity = {
            VulnerabilityLevel.CRITICAL: [],
            VulnerabilityLevel.HIGH: [],
            VulnerabilityLevel.MEDIUM: [],
            VulnerabilityLevel.LOW: [],
            VulnerabilityLevel.INFO: []
        }
        
        for finding in all_findings:
            findings_by_severity[finding.level].append(finding.to_dict())
        
        # Calculate execution time
        execution_time = (datetime.utcnow() - start_time).total_seconds()
        
        # Record telemetry
        telemetry = get_telemetry_manager()
        if telemetry:
            telemetry.record_custom_metric(
                name="security_scan_findings_count",
                value=len(all_findings),
                attributes={
                    "critical": len(findings_by_severity[VulnerabilityLevel.CRITICAL]),
                    "high": len(findings_by_severity[VulnerabilityLevel.HIGH]),
                    "medium": len(findings_by_severity[VulnerabilityLevel.MEDIUM]),
                    "low": len(findings_by_severity[VulnerabilityLevel.LOW])
                }
            )
        
        # Create summary
        summary = {
            "timestamp": datetime.utcnow().isoformat(),
            "execution_time_seconds": round(execution_time, 3),
            "total_findings": len(all_findings),
            "findings_by_severity": {
                "critical": len(findings_by_severity[VulnerabilityLevel.CRITICAL]),
                "high": len(findings_by_severity[VulnerabilityLevel.HIGH]),
                "medium": len(findings_by_severity[VulnerabilityLevel.MEDIUM]),
                "low": len(findings_by_severity[VulnerabilityLevel.LOW]),
                "info": len(findings_by_severity[VulnerabilityLevel.INFO])
            },
            "findings": {
                "critical": findings_by_severity[VulnerabilityLevel.CRITICAL],
                "high": findings_by_severity[VulnerabilityLevel.HIGH],
                "medium": findings_by_severity[VulnerabilityLevel.MEDIUM],
                "low": findings_by_severity[VulnerabilityLevel.LOW],
                "info": findings_by_severity[VulnerabilityLevel.INFO]
            }
        }
        
        # Save scan results to Redis with 30-day expiration
        scan_id = f"security:scan:{datetime.utcnow().isoformat()}"
        await self.redis.set(
            scan_id,
            json.dumps(summary),
            ex=60*60*24*30  # 30 days
        )
        
        # Add to scan history index
        await self.redis.lpush("security:scans", scan_id)
        await self.redis.ltrim("security:scans", 0, 99)  # Keep last 100 scans
        
        self._logger.info(f"Security scan completed: {len(all_findings)} findings")
        
        return summary


# Singleton instance
_security_scanner: Optional[SecurityScanner] = None


async def get_security_scanner(app: FastAPI, redis: Redis) -> SecurityScanner:
    """Get the global security scanner instance."""
    global _security_scanner
    if _security_scanner is None:
        _security_scanner = SecurityScanner(app=app, redis=redis)
    return _security_scanner
