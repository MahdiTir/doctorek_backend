from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..utils import get_user_id_from_token

from ..models import (
    Profiles,
)
from ..serializers import (
    ProfileSerializer,
)


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profiles.objects.all()
    serializer_class = ProfileSerializer
    #permission_classes = [IsAuthenticated]


class ProfileUpdateView(APIView):
    def patch(self, request):
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({"detail": "Unauthorized"}, status=status.HTTP_401_UNAUTHORIZED)  
        try:
            profile = Profiles.objects.get(id=user_id)
        except Profiles.DoesNotExist:
            return Response({"detail": "Profile not found"}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = ProfileSerializer(profile, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get(self, request):
        user_id = get_user_id_from_token(request)
        if not user_id:
            return Response({
                'success': False,
                'message': 'Invalid Token.',
                'data': None
            }, status=401)
        try:
            profile = Profiles.objects.get(id=user_id)
        except Profiles.DoesNotExist:
            return Response({
                'success': False,
                'message': 'Profile not found.',
                'data': None
            }, status=404)
        
        serialized = ProfileSerializer(profile)
        return Response({
                'success': True,
                'message': 'Profile fetched successfully.',
                'data': serialized.data
            }, status=200)
        
