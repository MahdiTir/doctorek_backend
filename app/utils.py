
import requests
from django.conf import settings

def verify_token(token):
    """
    Verify a JWT token with Supabase authentication API
    
    Args:
        token (str): The JWT token to verify
        
    Returns:
        dict or None: User data if token is valid, None if invalid
    """
    if not token:
        return None
        
    try:
        # Clean the token if it has the "Bearer " prefix
        if token.startswith('Bearer '):
            token = token.split(' ')[1]
            
        # Call Supabase auth API to verify token and get user
        response = requests.get(
            f"{settings.SUPABASE_URL}/auth/v1/user",
            headers={
                'apikey': settings.SUPABASE_KEY,
                'Authorization': f'Bearer {token}'
            }
        )
        
        # If request is successful, return the user data
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Token verification failed: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error verifying token: {str(e)}")
        return None

def get_user_id_from_token(request):
    """
    Extract and verify user ID from authentication token in request
    
    Args:
        request: Django/DRF request object
        
    Returns:
        str or None: User ID if token is valid, None otherwise
    """
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if not auth_header:
        return None
        
    # Extract token from auth header
    if ' ' in auth_header:
        _, token = auth_header.split(' ', 1)
    else:
        token = auth_header
        
    # Verify token with Supabase
    user_data = verify_token(token)
    
    if user_data and 'id' in user_data:
        return user_data['id']
    
    return None
