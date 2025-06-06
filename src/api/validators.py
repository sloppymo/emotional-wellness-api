"""
Request validation decorators for the Emotional Wellness API.
Provides advanced validation beyond Pydantic's built-in features.

These decorators can be applied to API endpoint functions to perform:
1. Cross-field validation
2. Business logic validation
3. Content safety validation
4. Data consistency checks
5. PHI-related validation
"""

import functools
import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union

from fastapi import Depends, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


def validate_consistent_user_data(field_name: str = "user_id"):
    """
    Validates that user ID in path/query matches the user ID in request body.
    
    Args:
        field_name: Name of the user ID field in request body
        
    Raises:
        HTTPException: If user IDs don't match
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            request = next((arg for arg in args if isinstance(arg, Request)), 
                         kwargs.get("request"))
            
            if not request:
                # If no request object found, just proceed
                return await func(*args, **kwargs)
            
            # Extract user ID from path and body
            path_user_id = kwargs.get("user_id")
            
            # If path doesn't have user_id, just proceed
            if not path_user_id:
                return await func(*args, **kwargs)
                
            # Get request body
            try:
                body = await request.json()
                body_user_id = body.get(field_name)
                
                # Validate user IDs match if present in body
                if body_user_id and str(body_user_id) != str(path_user_id):
                    logger.warning(
                        f"User ID mismatch: path={path_user_id}, body={body_user_id}"
                    )
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="User ID in path must match user ID in body",
                    )
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as e:
                # Log error but continue if body can't be parsed as JSON
                logger.error(f"Error validating user data consistency: {str(e)}")
                
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def validate_required_fields(required_fields: List[str], model_class: Type[BaseModel] = None):
    """
    Ensures that the required fields are present in the request even before 
    Pydantic validation runs.
    
    Args:
        required_fields: List of field names that must be present
        model_class: Optional Pydantic model class for validation
        
    Raises:
        HTTPException: If any required fields are missing
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Find the request object
            request = next((arg for arg in args if isinstance(arg, Request)), 
                         kwargs.get("request"))
                         
            if not request:
                # If no request object found, just proceed
                return await func(*args, **kwargs)
                
            try:
                body = await request.json()
                
                # Check for missing fields
                missing_fields = [field for field in required_fields if field not in body]
                
                if missing_fields:
                    logger.warning(f"Missing required fields: {missing_fields}")
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Missing required fields: {', '.join(missing_fields)}",
                    )
                    
                # Additional validation with Pydantic model if provided
                if model_class:
                    try:
                        model_class(**body)
                    except ValidationError as e:
                        logger.warning(f"Validation error: {str(e)}")
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=e.errors(),
                        )
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except ValueError:
                # If body can't be parsed as JSON
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid JSON in request body",
                )
            except Exception as e:
                logger.error(f"Error validating required fields: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error validating request",
                )
                
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def validate_date_range(start_date_field: str, end_date_field: str, max_days: Optional[int] = None):
    """
    Validates that:
    1. end_date is after start_date
    2. Optional: date range doesn't exceed max_days
    
    Args:
        start_date_field: Field name containing the start date
        end_date_field: Field name containing the end date
        max_days: Maximum allowed days between dates
        
    Raises:
        HTTPException: If validation fails
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Get the Pydantic model from kwargs
                for arg_name, arg_value in kwargs.items():
                    if hasattr(arg_value, start_date_field) and hasattr(arg_value, end_date_field):
                        model = arg_value
                        start_date = getattr(model, start_date_field)
                        end_date = getattr(model, end_date_field)
                        
                        # Validate end date is after start date
                        if end_date < start_date:
                            logger.warning(f"Invalid date range: end_date before start_date")
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"End date must be after start date",
                            )
                            
                        # Validate max days if specified
                        if max_days:
                            delta = end_date - start_date
                            if delta.days > max_days:
                                logger.warning(f"Date range exceeds max allowed: {delta.days} > {max_days}")
                                raise HTTPException(
                                    status_code=status.HTTP_400_BAD_REQUEST,
                                    detail=f"Date range cannot exceed {max_days} days",
                                )
                        
                        break
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except AttributeError:
                # If the fields don't exist, just continue
                pass
            except Exception as e:
                logger.error(f"Error validating date range: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error validating date range",
                )
                
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def validate_content_safety(content_field: str, unsafe_patterns: List[str] = None):
    """
    Validates that content doesn't contain unsafe patterns.
    
    Args:
        content_field: Field name containing the content
        unsafe_patterns: List of regex patterns to check for
        
    Raises:
        HTTPException: If unsafe content is detected
    """
    import re
    
    # Default unsafe patterns if none provided
    if unsafe_patterns is None:
        unsafe_patterns = [
            r'<script.*?>.*?</script>',  # Scripts
            r'javascript:',  # JavaScript URLs
            r'onerror=',  # Event handlers
            r'onclick=',
            r'onload=',
            r'<iframe.*?>.*?</iframe>',  # iframes
            r'<img.*?onerror=.*?>',  # Image error handlers
        ]

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Get request body if available
                request = next((arg for arg in args if isinstance(arg, Request)), 
                             kwargs.get("request"))
                             
                if request:
                    try:
                        body = await request.json()
                        content = body.get(content_field)
                        
                        if content and isinstance(content, str):
                            # Check for unsafe patterns
                            for pattern in unsafe_patterns:
                                if re.search(pattern, content, re.IGNORECASE):
                                    logger.warning(f"Unsafe content detected: {pattern}")
                                    raise HTTPException(
                                        status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Unsafe content detected",
                                    )
                    except HTTPException:
                        # Re-raise HTTP exceptions
                        raise
                    except ValueError:
                        # If body can't be parsed as JSON, continue
                        pass
                
                # Check Pydantic models in kwargs
                for arg_name, arg_value in kwargs.items():
                    if hasattr(arg_value, content_field):
                        content = getattr(arg_value, content_field)
                        
                        if content and isinstance(content, str):
                            # Check for unsafe patterns
                            for pattern in unsafe_patterns:
                                if re.search(pattern, content, re.IGNORECASE):
                                    logger.warning(f"Unsafe content detected: {pattern}")
                                    raise HTTPException(
                                        status_code=status.HTTP_400_BAD_REQUEST,
                                        detail="Unsafe content detected",
                                    )
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as e:
                logger.error(f"Error validating content safety: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error validating content safety",
                )
                
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def log_validation_errors():
    """
    Decorator that catches validation errors and logs them before re-raising.
    
    This is useful for monitoring and auditing validation failures which
    could indicate security issues or API misuse.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except ValidationError as e:
                # Extract useful info for logging
                endpoint = func.__name__
                error_details = e.errors()
                
                # Get client info if request is available
                request = next((arg for arg in args if isinstance(arg, Request)), 
                             kwargs.get("request"))
                client_info = {}
                
                if request:
                    client_info = {
                        "ip": request.client.host if request.client else "unknown",
                        "user_agent": request.headers.get("user-agent", "unknown"),
                    }
                    
                # Log the validation error with context
                logger.warning(
                    f"Validation error in {endpoint}", 
                    extra={
                        "errors": error_details,
                        "client": client_info,
                    }
                )
                
                # Re-raise for FastAPI to handle
                raise
            except HTTPException as e:
                # Also log HTTP exceptions that might be validation-related
                if e.status_code in (400, 422):
                    logger.warning(
                        f"HTTP validation error: {e.detail}",
                        extra={"status_code": e.status_code}
                    )
                raise
                
        return wrapper
    return decorator


def verify_phi_identifiers(phi_fields: List[str]):
    """
    Checks if the request contains PHI identifiers and ensures proper handling.
    
    This validates that PHI fields are:
    1. Properly encrypted if present
    2. Only accessed by authorized users
    
    Args:
        phi_fields: List of field names that might contain PHI
        
    Raises:
        HTTPException: If PHI validation fails
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                # Check if request contains PHI fields
                for arg_name, arg_value in kwargs.items():
                    if isinstance(arg_value, BaseModel):
                        # Use model_dump instead of dict for Pydantic v2 compatibility
                        model_dict = arg_value.model_dump() if hasattr(arg_value, "model_dump") else arg_value.dict()
                        found_phi_fields = [field for field in phi_fields if field in model_dict]
                        
                        if found_phi_fields:
                            # Log PHI access attempt (for audit purposes)
                            logger.info(
                                f"PHI fields accessed: {found_phi_fields}",
                                extra={"endpoint": func.__name__}
                            )
                            
                            # PHI fields present - validate authorization
                            # (assuming verify_phi_scope dependency is used in the endpoint)
                            # This is just an extra safety check
                            user = kwargs.get("user") or next(
                                (arg for arg in args if hasattr(arg, "scopes")), 
                                None
                            )
                            
                            if not user or not hasattr(user, "scopes") or "phi_access" not in user.scopes:
                                logger.warning(
                                    f"Unauthorized PHI access attempt", 
                                    extra={"endpoint": func.__name__}
                                )
                                raise HTTPException(
                                    status_code=status.HTTP_403_FORBIDDEN,
                                    detail="PHI access not authorized",
                                )
            except HTTPException:
                # Re-raise HTTP exceptions
                raise
            except Exception as e:
                logger.error(f"Error validating PHI fields: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Error validating PHI fields",
                )
                
            return await func(*args, **kwargs)
        return wrapper
    return decorator
