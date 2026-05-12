from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.conf import settings
from .serializers import RegisterSerializer, LoginSerializer
from .models import User
import os


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        if User.objects.filter(email=request.data.get('email')).exists():
            return Response({'message': 'user with this email already exists'}, status=status.HTTP_409_CONFLICT)
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = serializer.validated_data['email']
        password = serializer.validated_data['password']

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'message': 'user not found'}, status=404)

        if user.is_google_auth:
            return Response({'message': 'this account uses Google login'}, status=400)

        user = authenticate(request, email=email, password=password)
        if not user:
            return Response({'message': 'invalid credentials'}, status=401)

        refresh = RefreshToken.for_user(user)

        response = Response({
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'message': 'login successful'
        })

        set_auth_cookies(
            response,
            str(refresh.access_token),
            str(refresh)
        )

        return response
    
class GoogleAuthView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        token = request.data.get('id_token')

        if not token:
            return Response({'message': 'id_token is required'}, status=400)

        try:
            google_data = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                os.getenv('GOOGLE_CLIENT_ID')
            )
        except ValueError:
            return Response({'message': 'invalid token'}, status=401)

        email = google_data.get('email')
        username = google_data.get('name', '').replace(' ', '_').lower()

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': username,
                'is_google_auth': True,
            }
        )

        refresh = RefreshToken.for_user(user)

        response = Response({
            'id': str(user.id),
            'email': user.email,
            'username': user.username,
            'message': 'login successful'
        })

        set_auth_cookies(
            response,
            str(refresh.access_token),
            str(refresh)
        )

        return response
    
class RefreshView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get("refresh")

        if not refresh_token:
            return Response({"message": "No refresh token"}, status=401)

        try:
            token = RefreshToken(refresh_token)
            access_token = str(token.access_token)

            response = Response({"message": "token refreshed"})
            response.set_cookie(
                key="access",
                value=access_token,
                httponly=True,
                secure=True,
                samesite="Lax",
            )
            return response

        except Exception:
            return Response({"message": "Invalid refresh token"}, status=401)
    
class LogoutView(APIView):
    def post(self, request):
        response = Response({"message": "logged out"})
        response.delete_cookie("access")
        response.delete_cookie("refresh")
        return response
    
def set_auth_cookies(response, access_token, refresh_token):
    response.set_cookie(
        key="access",
        value=access_token,
        httponly=True,
        secure=True,              # True in production (HTTPS)
        samesite="Lax",
        max_age=60 * 15,
    )
    response.set_cookie(
        key="refresh",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="Lax",
        max_age=60 * 60 * 24,
    )
    return response