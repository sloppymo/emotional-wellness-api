#!/usr/bin/env python3
"""
Comprehensive Security Audit Script for Emotional Wellness API

This script performs a thorough security audit, identifies vulnerabilities,
and provides actionable recommendations for fixing security issues.
"""

import os
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple
import json

class SecurityAuditor:
    """Comprehensive security auditor for the application."""
    
    def __init__(self):
        self.findings = []
        self.critical_findings = []
        self.high_findings = []
        self.medium_findings = []
        self.low_findings = []
        
    def add_finding(self, level: str, title: str, description: str, file_path: str = None, line_number: int = None, recommendation: str = None):
        """Add a security finding."""
        finding = {
            "level": level,
            "title": title,
            "description": description,
            "file_path": file_path,
            "line_number": line_number,
            "recommendation": recommendation
        }
        
        self.findings.append(finding)
        
        if level == "CRITICAL":
            self.critical_findings.append(finding)
        elif level == "HIGH":
            self.high_findings.append(finding)
        elif level == "MEDIUM":
            self.medium_findings.append(finding)
        elif level == "LOW":
            self.low_findings.append(finding)
    
    def scan_hardcoded_secrets(self):
        """Scan for hardcoded secrets and credentials."""
        print("🔍 Scanning for hardcoded secrets...")
        
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']{8,}["\']', "Hardcoded password found"),
            (r'secret\s*=\s*["\'][^"\']{16,}["\']', "Hardcoded secret found"),
            (r'api_key\s*=\s*["\'][^"\']{16,}["\']', "Hardcoded API key found"),
            (r'token\s*=\s*["\'][^"\']{16,}["\']', "Hardcoded token found"),
            (r'key\s*=\s*["\'][^"\']{32,}["\']', "Hardcoded encryption key found"),
            (r'sk-[a-zA-Z0-9]{32,}', "OpenAI API key pattern found"),
            (r'ghp_[a-zA-Z0-9]{36}', "GitHub personal access token found"),
            (r'AKIA[0-9A-Z]{16}', "AWS access key ID found")
        ]
        
        for root, dirs, files in os.walk('.'):
            # Skip virtual environments and common non-source directories
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv', 'env']]
            
            for file in files:
                if file.endswith(('.py', '.js', '.ts', '.json', '.yml', '.yaml', '.env.example')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            lines = content.split('\n')
                            
                            for i, line in enumerate(lines, 1):
                                for pattern, description in secret_patterns:
                                    if re.search(pattern, line, re.IGNORECASE):
                                        # Skip if it's in a comment or obviously a placeholder
                                        if ('example' in line.lower() or 
                                            'placeholder' in line.lower() or 
                                            'your_' in line.lower() or
                                            'replace' in line.lower() or
                                            line.strip().startswith('#') or
                                            line.strip().startswith('//')):
                                            continue
                                            
                                        self.add_finding(
                                            "CRITICAL",
                                            description,
                                            f"Potential hardcoded secret in line: {line.strip()}",
                                            file_path,
                                            i,
                                            "Move sensitive values to environment variables or secure configuration files"
                                        )
                    except Exception as e:
                        continue
    
    def scan_environment_variables(self):
        """Scan environment variable configuration."""
        print("🔍 Scanning environment variables...")
        
        # Check for missing critical environment variables
        critical_env_vars = [
            "JWT_SECRET_KEY",
            "PHI_ENCRYPTION_KEY", 
            "API_KEY",
            "POSTGRES_PASSWORD"
        ]
        
        for var in critical_env_vars:
            if not os.environ.get(var):
                self.add_finding(
                    "HIGH",
                    f"Missing Critical Environment Variable: {var}",
                    f"The {var} environment variable is not set, which may cause security issues",
                    recommendation=f"Set {var} environment variable with a secure value"
                )
        
        # Check for weak environment variable values
        jwt_secret = os.environ.get("JWT_SECRET_KEY", "")
        if jwt_secret and len(jwt_secret) < 32:
            self.add_finding(
                "CRITICAL",
                "Weak JWT Secret Key",
                f"JWT secret key is only {len(jwt_secret)} characters long",
                recommendation="Use a JWT secret key with at least 32 random characters"
            )
        
        # Check for debug mode in production-like environment
        if os.environ.get("DEBUG", "").lower() == "true":
            self.add_finding(
                "MEDIUM",
                "Debug Mode Enabled",
                "Application is running in debug mode",
                recommendation="Disable debug mode in production environments"
            )
        
        # Check CORS configuration
        allowed_origins = os.environ.get("ALLOWED_ORIGINS", "*")
        if allowed_origins == "*":
            self.add_finding(
                "HIGH",
                "Permissive CORS Policy",
                "CORS is configured to allow requests from any origin",
                recommendation="Restrict ALLOWED_ORIGINS to specific required domains"
            )
    
    def scan_file_permissions(self):
        """Scan for insecure file permissions."""
        print("🔍 Scanning file permissions...")
        
        sensitive_files = [
            ".env",
            "config.py",
            "settings.py",
            "requirements.txt"
        ]
        
        for root, dirs, files in os.walk('.'):
            for file in files:
                if file in sensitive_files or file.endswith('.key') or file.endswith('.pem'):
                    file_path = os.path.join(root, file)
                    try:
                        # Check if file is world-readable
                        stat_info = os.stat(file_path)
                        permissions = oct(stat_info.st_mode)[-3:]
                        
                        if permissions[2] != '0':  # Others have read permission
                            self.add_finding(
                                "MEDIUM",
                                "Insecure File Permissions",
                                f"File {file_path} is world-readable (permissions: {permissions})",
                                file_path,
                                recommendation=f"Change file permissions: chmod 600 {file_path}"
                            )
                    except Exception:
                        continue
    
    def scan_dependencies(self):
        """Scan for vulnerable dependencies."""
        print("🔍 Scanning dependencies for vulnerabilities...")
        
        # Check if pip-audit is available
        try:
            result = subprocess.run(['pip-audit', '--format=json'], 
                                 capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                vulnerabilities = json.loads(result.stdout)
                for vuln in vulnerabilities:
                    self.add_finding(
                        "HIGH",
                        f"Vulnerable Dependency: {vuln.get('package', 'Unknown')}",
                        f"Version {vuln.get('installed_version')} has known vulnerability: {vuln.get('description', 'No description')}",
                        recommendation=f"Update to version {vuln.get('fixed_versions', ['latest'])[0]} or later"
                    )
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
            self.add_finding(
                "LOW",
                "Dependency Scanning Unavailable",
                "pip-audit is not installed or failed to run",
                recommendation="Install pip-audit: pip install pip-audit"
            )
    
    def scan_sql_injection_patterns(self):
        """Scan for potential SQL injection vulnerabilities."""
        print("🔍 Scanning for SQL injection patterns...")
        
        sql_injection_patterns = [
            r'f["\'].*SELECT.*{.*}.*["\']',  # f-string SQL
            r'["\'].*SELECT.*%.*["\']',      # % formatting
            r'["\'].*SELECT.*\+.*["\']',     # String concatenation
            r'\.format\(.*SELECT.*\)',       # .format() with SQL
            r'execute\(["\'].*\+.*["\']',    # execute with concatenation
        ]
        
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']]
            
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            lines = content.split('\n')
                            
                            for i, line in enumerate(lines, 1):
                                for pattern in sql_injection_patterns:
                                    if re.search(pattern, line, re.IGNORECASE):
                                        self.add_finding(
                                            "HIGH",
                                            "Potential SQL Injection",
                                            f"Potential SQL injection pattern in line: {line.strip()}",
                                            file_path,
                                            i,
                                            "Use parameterized queries or ORM methods instead of string concatenation"
                                        )
                    except Exception:
                        continue
    
    def scan_xss_patterns(self):
        """Scan for potential XSS vulnerabilities."""
        print("🔍 Scanning for XSS patterns...")
        
        xss_patterns = [
            r'render_template_string\(',
            r'Markup\(',
            r'|safe',
            r'innerHTML.*=',
            r'document\.write\(',
        ]
        
        for root, dirs, files in os.walk('.'):
            dirs[:] = [d for d in dirs if d not in ['.git', '__pycache__', 'node_modules', '.venv', 'venv']]
            
            for file in files:
                if file.endswith(('.py', '.html', '.js', '.ts')):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                            content = f.read()
                            lines = content.split('\n')
                            
                            for i, line in enumerate(lines, 1):
                                for pattern in xss_patterns:
                                    if re.search(pattern, line, re.IGNORECASE):
                                        self.add_finding(
                                            "MEDIUM",
                                            "Potential XSS Vulnerability",
                                            f"Potential XSS pattern in line: {line.strip()}",
                                            file_path,
                                            i,
                                            "Ensure proper input validation and output encoding"
                                        )
                    except Exception:
                        continue
    
    def generate_report(self):
        """Generate a comprehensive security report."""
        print("\n" + "="*60)
        print("🛡️  SECURITY AUDIT REPORT")
        print("="*60)
        
        print(f"\n📊 SUMMARY:")
        print(f"   🔴 Critical: {len(self.critical_findings)}")
        print(f"   🟠 High: {len(self.high_findings)}")
        print(f"   🟡 Medium: {len(self.medium_findings)}")
        print(f"   🟢 Low: {len(self.low_findings)}")
        print(f"   📋 Total: {len(self.findings)}")
        
        # Critical findings
        if self.critical_findings:
            print(f"\n🔴 CRITICAL FINDINGS ({len(self.critical_findings)}):")
            for i, finding in enumerate(self.critical_findings, 1):
                print(f"\n   {i}. {finding['title']}")
                print(f"      Description: {finding['description']}")
                if finding['file_path']:
                    print(f"      File: {finding['file_path']}")
                    if finding['line_number']:
                        print(f"      Line: {finding['line_number']}")
                if finding['recommendation']:
                    print(f"      Fix: {finding['recommendation']}")
        
        # High findings
        if self.high_findings:
            print(f"\n🟠 HIGH FINDINGS ({len(self.high_findings)}):")
            for i, finding in enumerate(self.high_findings, 1):
                print(f"\n   {i}. {finding['title']}")
                print(f"      Description: {finding['description']}")
                if finding['file_path']:
                    print(f"      File: {finding['file_path']}")
                if finding['recommendation']:
                    print(f"      Fix: {finding['recommendation']}")
        
        # Medium findings (abbreviated)
        if self.medium_findings:
            print(f"\n🟡 MEDIUM FINDINGS ({len(self.medium_findings)}):")
            for i, finding in enumerate(self.medium_findings[:5], 1):  # Show first 5
                print(f"   {i}. {finding['title']}")
            if len(self.medium_findings) > 5:
                print(f"   ... and {len(self.medium_findings) - 5} more")
        
        print(f"\n🎯 PRIORITY ACTIONS:")
        print(f"   1. Fix all {len(self.critical_findings)} critical findings immediately")
        print(f"   2. Address {len(self.high_findings)} high-priority security issues")
        print(f"   3. Review and fix medium-priority findings")
        print(f"   4. Implement security monitoring and alerting")
        
        print(f"\n📝 DETAILED REPORT:")
        print(f"   Full findings saved to: security_audit_report.json")
        
        # Save detailed report
        with open('security_audit_report.json', 'w') as f:
            json.dump(self.findings, f, indent=2)
    
    def run_full_audit(self):
        """Run the complete security audit."""
        print("🚀 Starting comprehensive security audit...")
        
        self.scan_hardcoded_secrets()
        self.scan_environment_variables()
        self.scan_file_permissions()
        self.scan_dependencies()
        self.scan_sql_injection_patterns()
        self.scan_xss_patterns()
        
        self.generate_report()

if __name__ == "__main__":
    auditor = SecurityAuditor()
    auditor.run_full_audit() 