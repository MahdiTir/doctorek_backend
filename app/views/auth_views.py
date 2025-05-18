from rest_framework.views import APIView
from rest_framework.response import Response
import requests
from django.conf import settings

class LoginView(APIView):
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'detail': 'Email and password are required.'}, status=400)

        response = requests.post(
            f"{settings.SUPABASE_URL}/auth/v1/token?grant_type=password",
            headers={
                'apikey': settings.SUPABASE_KEY,
                'Content-Type': 'application/json'
            },
            json={'email': email, 'password': password}
        )

        if response.status_code == 200:
            return Response(response.json())  
        else:
            return Response(response.json(), status=response.status_code)


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
            return Response(response.json(), status=response.status_code)
        
        
        user = response.json().get("user")
        if not user:
            return Response({"detail": "User created but no user data returned."}, status=500)

        user_id = user["id"]

        if user_type:
            patch = requests.patch(
                f"{settings.SUPABASE_URL}/rest/v1/profiles?id=eq.{user_id}",
                headers={
                    "apikey": settings.SUPABASE_KEY,
                    "Authorization": f"Bearer {settings.SUPABASE_KEY}",
                    "Content-Type": "application/json",
                    "Prefer": "return=representation"
                },
                json={"user_type": user_type}
            )

            if patch.status_code not in (200, 204):
                return Response({
                    "detail": "User created but failed to update user_type in profile.",
                    "error": patch.json()
                }, status=500)

        return Response({"user": user}, status=201)
