from django.contrib.auth import login, logout
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import ensure_csrf_cookie
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import UserSerializer, RegisterSerializer, LoginSerializer


class CSRFTokenView(APIView):
    """
    Ensures CSRF cookie is set and returns the CSRF token.
    """
    permission_classes = [AllowAny]

    @method_decorator(ensure_csrf_cookie)
    def get(self, request):
        return Response({
            'csrfToken': get_token(request),
            'detail': 'CSRF cookie established.'
        })


class RegisterView(APIView):
    """
    API endpoint for public user registration (Buyer or Seller).
    Automatically authenticates the newly created user session.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Establish Django login session
            login(request, user)
            user_data = UserSerializer(user).data
            return Response({
                'message': 'Account created successfully! Welcome to Bliss Card.',
                'user': user_data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    """
    API endpoint for user authentication with session management.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            login(request, user)
            user_data = UserSerializer(user).data

            # Determine appropriate redirect based on role
            redirect_url = '/'
            if user.role == 'admin':
                redirect_url = '/admin-dashboard/'
            elif user.role == 'seller':
                redirect_url = '/seller-dashboard/'

            return Response({
                'message': f'Welcome back, {user.username}!',
                'user': user_data,
                'redirect_url': redirect_url
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    """
    API endpoint to terminate current session.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        username = request.user.username
        logout(request)
        return Response({
            'message': f'User {username} has been logged out.'
        }, status=status.HTTP_200_OK)


class CurrentUserView(APIView):
    """
    Returns current user info and authentication state.
    """
    permission_classes = [AllowAny]

    def get(self, request):
        if request.user.is_authenticated:
            return Response({
                'authenticated': True,
                'user': UserSerializer(request.user).data
            })
        return Response({
            'authenticated': False,
            'user': None
        })
