#!/usr/bin/env python3
"""
Script to add blunt, helpful comments throughout the emotional wellness API codebase.
Makes the code more human and workable.
"""

import os
import re
from pathlib import Path

# Comment templates for different types of files
COMMENT_TEMPLATES = {
    'hipaa': {
        'file_header': "# hipaa compliance stuff - the lawyers made us do this",
        'patterns': {
            'PHI_PATTERNS': "# regex patterns to find personal info we shouldn't log",
            'check_processor': "# make sure a processor doesn't leak personal data",
            'check_output': "# scan output for personal info before sending",
            'clean_phi': "# replace personal info with [REDACTED] - privacy protection",
            'audit_log': "# log actions for compliance audits - metadata only"
        }
    },
    'auth': {
        'file_header': "# authentication and authorization - who can access what",
        'patterns': {
            'get_api_key': "# validate api key from header - basic auth layer",
            'create_access_token': "# make jwt tokens for users - session management",
            'get_current_user': "# decode jwt and check permissions - the auth bouncer",
            'verify_phi_scope': "# extra check for accessing personal health info"
        }
    },
    'clinical': {
        'file_header': "# clinical portal endpoints - for healthcare providers",
        'patterns': {
            'get_dashboard_summary': "# overview of all patients and alerts - management view",
            'get_active_alerts': "# current crisis situations that need attention",
            'acknowledge_alert': "# mark alert as seen by clinician - audit trail",
            'create_intervention': "# record what action was taken for a patient",
            'update_intervention_status': "# track progress of interventions"
        }
    },
    'exceptions': {
        'file_header': "# custom exceptions for better error handling",
        'patterns': {
            'BaseAPIException': "# base class for all our custom errors",
            'AuthenticationError': "# when login fails - wrong password, expired token, etc",
            'ClinicalError': "# when something goes wrong in clinical processing",
            'CrisisDetectionError': "# when crisis detection fails - this is bad",
            'RateLimitError': "# when someone hits the api too fast"
        }
    }
}

def add_comments_to_file(file_path: str, comment_type: str):
    """Add comments to a specific file based on its type."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Get comment template for this file type
        template = COMMENT_TEMPLATES.get(comment_type, {})
        
        # Add file header comment if docstring exists
        if '"""' in content and 'file_header' in template:
            # Find the end of the first docstring
            docstring_end = content.find('"""', content.find('"""') + 3) + 3
            if docstring_end > 2:
                # Insert comment after docstring
                before = content[:docstring_end]
                after = content[docstring_end:]
                content = before + f"\n\n{template['file_header']}\n" + after
        
        # Add inline comments for specific patterns
        if 'patterns' in template:
            for pattern, comment in template['patterns'].items():
                # Look for function/class definitions
                regex = rf'(def {pattern}|class {pattern})'
                if re.search(regex, content):
                    # Add comment before the definition
                    content = re.sub(
                        rf'(\s*)(def {pattern}|class {pattern})',
                        rf'\1{comment}\n\1\2',
                        content
                    )
        
        # Write back to file
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"Added comments to {file_path}")
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def find_files_to_comment():
    """Find all Python files that need comments."""
    src_dir = Path("src")
    files_to_process = []
    
    # Map file patterns to comment types
    file_mappings = {
        'hipaa.py': 'hipaa',
        'auth.py': 'auth', 
        'clinical.py': 'clinical',
        'exceptions.py': 'exceptions'
    }
    
    # Find files recursively
    for py_file in src_dir.rglob("*.py"):
        file_name = py_file.name
        if file_name in file_mappings:
            files_to_process.append((str(py_file), file_mappings[file_name]))
    
    return files_to_process

def add_general_comments():
    """Add general helpful comments to key files."""
    
    # Add comments to specific files with custom logic
    files_with_custom_comments = [
        ("src/utils/hipaa.py", [
            ("class HIPAACompliance:", "# the compliance police - makes sure we don't leak personal info"),
            ("PHI_PATTERNS = [", "# regex patterns to catch personal data - ssn, phone, email, etc"),
            ("def check_processor", "# verify a processor won't leak personal data"),
            ("def clean_phi", "# scrub personal info from text before logging"),
            ("def audit_log", "# log actions for hipaa audits - lawyers love this")
        ]),
        
        ("src/security/auth.py", [
            ("api_key_header = APIKeyHeader", "# api key from request header - first auth layer"),
            ("oauth2_scheme = OAuth2PasswordBearer", "# jwt token auth - second auth layer"),
            ("async def get_api_key", "# validate the api key - basic auth check"),
            ("def create_access_token", "# make jwt tokens for authenticated users"),
            ("async def get_current_user", "# decode jwt and verify permissions - the main auth function")
        ]),
        
        ("src/routers/clinical.py", [
            ("@router.get(\"/dashboard\"", "# main dashboard for clinicians - overview of everything"),
            ("@router.get(\"/alerts\"", "# active crisis alerts that need attention"),
            ("@router.post(\"/alerts/{alert_id}/acknowledge\"", "# mark alert as seen - audit trail"),
            ("@router.post(\"/interventions\"", "# record what action was taken"),
            ("@router.put(\"/interventions/{intervention_id}/status\"", "# update intervention progress")
        ])
    ]
    
    for file_path, comments in files_with_custom_comments:
        try:
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    content = f.read()
                
                # Add each comment
                for pattern, comment in comments:
                    if pattern in content:
                        # Add comment on the line before the pattern
                        content = content.replace(
                            pattern,
                            f"    {comment}\n    {pattern}"
                        )
                
                with open(file_path, 'w') as f:
                    f.write(content)
                
                print(f"Added custom comments to {file_path}")
        except Exception as e:
            print(f"Error adding comments to {file_path}: {e}")

def add_comments_to_hipaa():
    """Add comments to HIPAA utilities."""
    file_path = "src/utils/hipaa.py"
    if not os.path.exists(file_path):
        return
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Add specific comments
        replacements = [
            ('"""HIPAA compliance utilities for the CANOPY system."""', 
             '"""HIPAA compliance utilities for the CANOPY system.\n\nbasically the compliance police - makes sure we don\'t leak personal info\n"""'),
            ('# PHI patterns', '# regex patterns to catch personal data - ssn, phone, email, names, dates'),
            ('def check_processor(cls, processor: Any) -> bool:', 
             'def check_processor(cls, processor: Any) -> bool:\n        """Check if a processor is HIPAA compliant - verify it won\'t leak personal data"""'),
            ('def clean_phi(cls, text: str) -> str:', 
             'def clean_phi(cls, text: str) -> str:\n        """Clean PHI from text - replace personal info with [REDACTED]"""'),
            ('def audit_log(cls,', 
             'def audit_log(cls,\n                 # log actions for hipaa audits - lawyers love this')
        ]
        
        for old, new in replacements:
            if old in content:
                content = content.replace(old, new)
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"Added comments to {file_path}")
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def add_comments_to_auth():
    """Add comments to auth module."""
    file_path = "src/security/auth.py"
    if not os.path.exists(file_path):
        return
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Add specific comments
        replacements = [
            ('# Security scheme definitions', '# Security scheme definitions - the auth layers'),
            ('api_key_header = APIKeyHeader', '# api key from request header - first auth layer\napi_key_header = APIKeyHeader'),
            ('oauth2_scheme = OAuth2PasswordBearer', '# jwt token auth - second auth layer\noauth2_scheme = OAuth2PasswordBearer'),
            ('async def get_api_key(api_key: str = Security(api_key_header)) -> str:', 
             'async def get_api_key(api_key: str = Security(api_key_header)) -> str:\n    """\n    Validate API key from header - basic auth check\n    \n    In production, this would validate against a secure database\n    with rate limiting and proper key rotation.\n    \n    for now just check against env var - simple but works\n    """'),
            ('def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:', 
             'def create_access_token(data: Dict, expires_delta: Optional[timedelta] = None) -> str:\n    """\n    Create a JWT access token - session management\n    \n    Args:\n        data: Data to encode in token\n        expires_delta: Token expiration time\n        \n    Returns:\n        Encoded JWT token string\n        \n    basically make a signed token that proves who you are\n    """')
        ]
        
        for old, new in replacements:
            if old in content:
                content = content.replace(old, new)
        
        with open(file_path, 'w') as f:
            f.write(content)
        
        print(f"Added comments to {file_path}")
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def main():
    """Main function to add comments throughout the codebase."""
    print("Adding blunt, helpful comments throughout the codebase...")
    
    # Add general comments to key files
    add_general_comments()
    
    # Add comments to specific files
    add_comments_to_hipaa()
    add_comments_to_auth()
    
    # Process files with templates
    files_to_process = find_files_to_comment()
    
    for file_path, comment_type in files_to_process:
        add_comments_to_file(file_path, comment_type)
    
    print("\nComment addition complete!")
    print("The codebase should now be more human and workable.")

if __name__ == "__main__":
    main() 