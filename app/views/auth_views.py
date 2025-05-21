from rest_framework.views import APIView
from rest_framework.response import Response
import requests
from django.conf import settings

class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({
                'success': False,
                'message': 'Email and password are required.',
                'data': None
            }, status=400)

        response = requests.post(
            f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers={
                'apikey': settings.SUPABASE_KEY,
                'Content-Type': 'application/json'
            },
            json={'email': email, 'password': password}
        )

        if response.status_code == 200:
            response_data = response.json()
            # Extract user ID from the response
            user_id = response_data.get('user', {}).get('id')
            
            formatted_response = {
                'success': True,
                'message': 'Login successful',
                'data': {
                    'access_token': response_data.get('access_token'),
                    'refresh_token': response_data.get('refresh_token'),
                    'userId': user_id,
                    'expires_in': response_data.get('expires_in'),
                    'expires_at': response_data.get('expires_at'),
                    'token_type': response_data.get('token_type')
                }
            }
            return Response(formatted_response)
        else:
            error_data = response.json()
            error_message = error_data.get('error_code', 'Login failed')
            
            return Response({
                'success': False,
                'message': error_message,
                'data': None
            }, status=response.status_code)


class SignUpView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        user_type = request.data.get("user_type") 

        if not email or not password:
            return Response({"detail": "Email and password are required."}, status=400)

        payload = {
            "email": email,
            "password": password,
        }

        if user_type:
            payload["data"] = {"user_type": user_type}

        response = requests.post(
            f"{settings.SUPABASE_URL}/auth/v1/signup",
            headers={
                "apikey": settings.SUPABASE_KEY,
                "Content-Type": "application/json"
            },
            json=payload
        )

        if response.status_code != 200:
            error_data = response.json()
            error_message = error_data.get('error_code', 'Signup failed')
            
            return Response({
                'success': False,
                'message': error_message,
                'data': None
            }, status=response.status_code)
        else :
            response_data = response.json()
            user_id = response_data.get('user', {}).get('id')
            
            formatted_response = {
                'success': True,
                'message': 'Signup successful',
                'data': {
                    'userId': user_id,
                    'access_token': response_data.get('access_token'),
                    'refresh_token': response_data.get('refresh_token'),
                    'expires_in': response_data.get('expires_in'),
                    'expires_at': response_data.get('expires_at'),
                    'token_type': response_data.get('token_type')
                }
            }
            return Response(formatted_response)

