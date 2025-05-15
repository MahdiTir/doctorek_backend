
import jwt

def get_user_id_from_token(request):
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    
    try:
        decoded = jwt.decode(token, options={"verify_signature": False})
        return decoded.get('sub') 
    except jwt.DecodeError:
        return None
