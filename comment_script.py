import os

# Add comments to HIPAA utilities
file_path = 'src/utils/hipaa.py'
if os.path.exists(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add specific comments
    if 'PHI patterns' in content and 'regex to catch' not in content:
        content = content.replace('# PHI patterns', '# PHI patterns - regex to catch personal data like ssn, phone, email')
    
    if 'def check_processor' in content and 'verify it won' not in content:
        content = content.replace(
            'def check_processor(cls, processor: Any) -> bool:',
            'def check_processor(cls, processor: Any) -> bool:\n        # verify a processor won\'t leak personal data'
        )
    
    if 'def clean_phi' in content and 'scrub personal info' not in content:
        content = content.replace(
            'def clean_phi(cls, text: str) -> str:',
            'def clean_phi(cls, text: str) -> str:\n        # scrub personal info from text before logging'
        )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print('Added comments to HIPAA utilities')

# Add comments to auth module  
file_path = 'src/security/auth.py'
if os.path.exists(file_path):
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Add specific comments
    if 'api_key_header = APIKeyHeader' in content and '# api key from' not in content:
        content = content.replace(
            'api_key_header = APIKeyHeader',
            '# api key from request header - first auth layer\napi_key_header = APIKeyHeader'
        )
    
    if 'oauth2_scheme = OAuth2PasswordBearer' in content and '# jwt token auth' not in content:
        content = content.replace(
            'oauth2_scheme = OAuth2PasswordBearer',
            '# jwt token auth - second auth layer\noauth2_scheme = OAuth2PasswordBearer'
        )
    
    with open(file_path, 'w') as f:
        f.write(content)
    
    print('Added comments to auth module')

print('Comment addition complete!') 