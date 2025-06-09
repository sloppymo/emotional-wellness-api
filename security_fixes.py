#!/usr/bin/env python3
"""
Security Fixes and Hardening Script

This script implements critical security fixes identified by the security audit.
"""

import os
import secrets
import string
import subprocess
import sys
from pathlib import Path

class SecurityFixer:
    """Implement security fixes and hardening."""
    
    def __init__(self):
        self.fixes_applied = []
        self.errors = []
    
    def generate_secure_key(self, length: int = 32) -> str:
        """Generate a cryptographically secure random key."""
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def create_secure_env_file(self):
        """Create a secure .env file if it doesn't exist."""
        print("🔧 Creating secure .env file...")
        
        if os.path.exists('.env'):
            print("   ⚠️  .env file already exists, skipping creation")
            return
        
        try:
            # Generate secure keys
            api_key = self.generate_secure_key(32)
            jwt_secret = self.generate_secure_key(64)
            phi_key = self.generate_secure_key(32)
            postgres_password = self.generate_secure_key(24)
            redis_password = self.generate_secure_key(24)
            
            env_content = f"""# Generated secure environment configuration
# Created by security_fixes.py on {os.popen('date').read().strip()}

# Environment
ENVIRONMENT=development
DEBUG=false

# Security Keys (Generated securely)
API_KEY={api_key}
JWT_SECRET_KEY={jwt_secret}
PHI_ENCRYPTION_KEY={phi_key}

# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=emotional_wellness
POSTGRES_USER=postgres
POSTGRES_PASSWORD={postgres_password}

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD={redis_password}
REDIS_DB=0

# CORS (restrict in production)
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000

# Rate Limiting
SKIP_RATE_LIMIT_SYSTEM=false

# Compliance
AUDIT_LOGGING_ENABLED=true
DATA_RETENTION_DAYS=2190

# Crisis Management
CRISIS_TEAM_EMAIL=crisis@organization.example
CRISIS_RESPONSE_SLA_SECONDS=180

# Admin Security
ADMIN_IP_WHITELIST=127.0.0.1,::1

# External APIs (set your real values)
ANTHROPIC_API_KEY=your_anthropic_api_key_here
"""
            
            with open('.env', 'w') as f:
                f.write(env_content)
            
            # Set secure permissions
            os.chmod('.env', 0o600)
            
            self.fixes_applied.append("Created secure .env file with generated keys")
            print("   ✅ Created .env file with secure generated keys")
            print("   🔒 Set file permissions to 600 (owner read/write only)")
            
        except Exception as e:
            error_msg = f"Failed to create .env file: {e}"
            self.errors.append(error_msg)
            print(f"   ❌ {error_msg}")
    
    def fix_file_permissions(self):
        """Fix insecure file permissions."""
        print("🔧 Fixing file permissions...")
        
        sensitive_files = [
            '.env',
            'env.example',
            'security_audit.py',
            'security_fixes.py'
        ]
        
        for file_path in sensitive_files:
            if os.path.exists(file_path):
                try:
                    # Set restrictive permissions (owner only)
                    os.chmod(file_path, 0o600)
                    self.fixes_applied.append(f"Fixed permissions for {file_path}")
                    print(f"   ✅ Set secure permissions for {file_path}")
                except Exception as e:
                    error_msg = f"Failed to fix permissions for {file_path}: {e}"
                    self.errors.append(error_msg)
                    print(f"   ❌ {error_msg}")
    
    def install_security_dependencies(self):
        """Install security scanning tools."""
        print("🔧 Installing security tools...")
        
        security_tools = [
            'pip-audit',
            'safety',
            'bandit'
        ]
        
        for tool in security_tools:
            try:
                print(f"   Installing {tool}...")
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', tool],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    self.fixes_applied.append(f"Installed security tool: {tool}")
                    print(f"   ✅ Installed {tool}")
                else:
                    error_msg = f"Failed to install {tool}: {result.stderr}"
                    self.errors.append(error_msg)
                    print(f"   ❌ {error_msg}")
                    
            except Exception as e:
                error_msg = f"Error installing {tool}: {e}"
                self.errors.append(error_msg)
                print(f"   ❌ {error_msg}")
    
    def create_security_headers_middleware(self):
        """Create security headers middleware."""
        print("🔧 Creating security headers middleware...")
        
        middleware_code = '''"""
Security headers middleware for enhanced API security.
"""

from fastapi import FastAPI, Request, Response
from fastapi.middleware.base import BaseHTTPMiddleware
from typing import Callable

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Security headers
        security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY", 
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Content-Security-Policy": "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()"
        }
        
        for header, value in security_headers.items():
            response.headers[header] = value
        
        # Remove server header for security by obscurity
        response.headers.pop("server", None)
        
        return response

def add_security_middleware(app: FastAPI) -> None:
    """Add security middleware to FastAPI app."""
    app.add_middleware(SecurityHeadersMiddleware)
'''
        
        try:
            middleware_path = Path("src/middleware/security_headers.py")
            middleware_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(middleware_path, 'w') as f:
                f.write(middleware_code)
            
            self.fixes_applied.append("Created security headers middleware")
            print("   ✅ Created security headers middleware")
            
        except Exception as e:
            error_msg = f"Failed to create security middleware: {e}"
            self.errors.append(error_msg)
            print(f"   ❌ {error_msg}")
    
    def create_input_validation_utils(self):
        """Create input validation utilities."""
        print("🔧 Creating input validation utilities...")
        
        validation_code = '''"""
Input validation utilities for preventing injection attacks.
"""

import re
import html
from typing import Any, List, Optional
from fastapi import HTTPException

class InputValidator:
    """Utilities for validating and sanitizing user input."""
    
    # SQL injection patterns
    SQL_INJECTION_PATTERNS = [
        r"('|(\\'))+.*(or|union|select|insert|update|delete|drop|create|alter)",
        r"(union|select|insert|update|delete|drop|create|alter).+",
        r"(exec|execute|sp_|xp_).+",
        r"(script|javascript|vbscript|onload|onerror|onclick).+"
    ]
    
    # XSS patterns
    XSS_PATTERNS = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"vbscript:",
        r"onload\\s*=",
        r"onerror\\s*=",
        r"onclick\\s*="
    ]
    
    @staticmethod
    def sanitize_string(value: str, max_length: int = 1000) -> str:
        """Sanitize string input to prevent XSS."""
        if not value:
            return ""
        
        # Truncate if too long
        if len(value) > max_length:
            value = value[:max_length]
        
        # HTML escape
        value = html.escape(value)
        
        # Remove potentially dangerous patterns
        for pattern in InputValidator.XSS_PATTERNS:
            value = re.sub(pattern, "", value, flags=re.IGNORECASE)
        
        return value.strip()
    
    @staticmethod
    def validate_sql_safe(value: str) -> bool:
        """Check if string is safe from SQL injection."""
        if not value:
            return True
        
        for pattern in InputValidator.SQL_INJECTION_PATTERNS:
            if re.search(pattern, value, re.IGNORECASE):
                return False
        
        return True
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format."""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    @staticmethod
    def validate_user_input(
        value: Any,
        field_name: str,
        max_length: int = 1000,
        required: bool = True,
        allow_sql: bool = False
    ) -> str:
        """Comprehensive input validation."""
        
        # Check if required
        if required and not value:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} is required"
            )
        
        if not value:
            return ""
        
        # Convert to string
        str_value = str(value)
        
        # Check length
        if len(str_value) > max_length:
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} exceeds maximum length of {max_length}"
            )
        
        # Check for SQL injection if not allowed
        if not allow_sql and not InputValidator.validate_sql_safe(str_value):
            raise HTTPException(
                status_code=400,
                detail=f"{field_name} contains potentially dangerous content"
            )
        
        # Sanitize and return
        return InputValidator.sanitize_string(str_value, max_length)

def validate_request_data(data: dict, validation_rules: dict) -> dict:
    """Validate request data according to rules."""
    validated_data = {}
    
    for field, rules in validation_rules.items():
        value = data.get(field)
        
        validated_data[field] = InputValidator.validate_user_input(
            value=value,
            field_name=field,
            max_length=rules.get("max_length", 1000),
            required=rules.get("required", True),
            allow_sql=rules.get("allow_sql", False)
        )
    
    return validated_data
'''
        
        try:
            validation_path = Path("src/utils/input_validation.py")
            validation_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(validation_path, 'w') as f:
                f.write(validation_code)
            
            self.fixes_applied.append("Created input validation utilities")
            print("   ✅ Created input validation utilities")
            
        except Exception as e:
            error_msg = f"Failed to create validation utilities: {e}"
            self.errors.append(error_msg)
            print(f"   ❌ {error_msg}")
    
    def generate_security_report(self):
        """Generate a security fixes report."""
        print("\n" + "="*60)
        print("🛡️  SECURITY FIXES APPLIED")
        print("="*60)
        
        print(f"\n✅ FIXES APPLIED ({len(self.fixes_applied)}):")
        for i, fix in enumerate(self.fixes_applied, 1):
            print(f"   {i}. {fix}")
        
        if self.errors:
            print(f"\n❌ ERRORS ENCOUNTERED ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                print(f"   {i}. {error}")
        
        print(f"\n🎯 NEXT STEPS:")
        print(f"   1. Review and customize the generated .env file")
        print(f"   2. Test the application with the new security settings")
        print(f"   3. Add the security middleware to your FastAPI app")
        print(f"   4. Use the input validation utilities in your endpoints")
        print(f"   5. Run regular security audits")
        
        print(f"\n📋 RECOMMENDATIONS:")
        print(f"   • Rotate the generated keys regularly (every 90 days)")
        print(f"   • Monitor logs for security events")
        print(f"   • Set up automated vulnerability scanning")
        print(f"   • Implement rate limiting on sensitive endpoints")
        print(f"   • Use HTTPS in production")
    
    def apply_all_fixes(self):
        """Apply all security fixes."""
        print("🚀 Applying security fixes...")
        
        self.create_secure_env_file()
        self.fix_file_permissions()
        self.install_security_dependencies()
        self.create_security_headers_middleware()
        self.create_input_validation_utils()
        
        self.generate_security_report()

if __name__ == "__main__":
    fixer = SecurityFixer()
    fixer.apply_all_fixes() 