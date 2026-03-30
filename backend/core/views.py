from django.contrib.auth import authenticate
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt
from rest_framework.response import Response
from .models import User
from .serializers import UserSerializer
from google.oauth2 import id_token
from google.auth.transport import requests
from rest_framework_simplejwt.tokens import RefreshToken
import os
from .user_stats import get_user_stats
import json
from baghchal.game_engine import get_user_by_username





@api_view(["POST"])
def signup(request):
    data = request.data
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    avatar = request.FILES.get("avatar")

    if not (username and password and email):
        print("incomplete data")
        return Response({"error": "incomplete data"}, status=400)

    if User.objects.filter(username=username).exists():
        print("username already taken")
        return Response({"error": "username already taken"}, status=400)
    if User.objects.filter(email=email).exists():
        print("email already registered")
        return Response({"error": "email already registered"}, status=400)

    user = User(username=username, email=email)
    user.set_password(password)
    user.avatar = avatar

    if not user:
        print("unable to signup")
        return Response({"error": "unable to signup"}, status=400)
    user.save()
    refresh = RefreshToken.for_user(user)
    serializer = UserSerializer(user, request)
    print("successfully signup")
    
    return Response({"user_data": serializer.data,
                     "access": str(refresh.access_token),
                     "refresh": str(refresh)
                     }, status=200)


@api_view(["POST"])
def login(request):
    data = request.data
    username = data.get("username")
    password = data.get("password")

    if not (username and password):
        return Response({"error": "usenrame and password required"}, status=400)

    user = authenticate(username=username, password=password)
    if user is None:
        print("no user")
        return Response({"error": "user doesn't exist"}, status=400)
    
    refresh = RefreshToken.for_user(user)
    serializer = UserSerializer(user, request)
     
    return Response({"user_data": serializer.data,
                     "access": str(refresh.access_token),
                     "refresh": str(refresh)
                     }, status=200)


@csrf_exempt
@api_view(["POST"])
def google_auth(request):
    token = request.data.get("token")
    mode = request.data.get("mode", "login")

    if not token:
        return Response({"error": "No token provided"}, status=400)
    try:
        # Verify the Google token
        client_id = os.environ.get("GOOGLE_CLIENT_ID")
        if not client_id:
            return Response({"error": "Google client ID not configured"},status=500)

        try:  
            idinfo = id_token.verify_oauth2_token(
                token, 
                requests.Request(), 
                client_id,
                clock_skew_in_seconds=30 # hopefully don't cause issue in production
            )
            print("Verification successful!")
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return Response({"error": str(e)}, status=400)

        email = idinfo['email']
        google_id = idinfo.get('sub')
        name = idinfo.get('name', '')
        picture = idinfo.get('picture', '')

        if not email:
            return Response({"error": "No email from google"}, status=400)

        try:
            user = User.objects.get(email=email)

            # authenticate the user but doesn't have password 
        except User.DoesNotExist: # if doesn't exist, create and login

            # Create new user from Google data
            username = email.split('@')[0] # Generate username from email
            
            user = User.objects.create(
                username=username,
                email=email,
                first_name=name.split()[0] if name else '',
                last_name=' '.join(name.split()[1:]) if len(name.split()) > 1 else ''
            )
            
            # Set unusable password since they're using Google OAuth
            user.set_unusable_password()
            user.save()

        # send user data for signup and login both 
        serializer = UserSerializer(user, request)
        refresh = RefreshToken.for_user(user) 

        return Response({"user_data": serializer.data,
                        "access": str(refresh.access_token),
                        "refresh": str(refresh)
                        }, status=200)
    
    except ValueError as e:
        print(f"ValueError: {str(e)}")
        return Response({"error": f"Invalid Google token: {str(e)}"}, status=400)
    except Exception as e:
        print(f"Exception: {str(e)}")
        return Response({"error": f"Authentication failed: {str(e)}"}, status=500)

@api_view(["POST"])
def guest_login(request):
    try: 
        guest_id = request.data.get("guest_id")  # frontend sends its generated guestId string
        if not guest_id:
            return Response({"error": "guest_id required"}, status=400)
        
        # Get or create the guest user
        user, created = User.objects.get_or_create(
            username=guest_id,
            defaults={"is_guest": True}
        )
        if created:
            user.set_unusable_password()
            user.save()
        
        refresh = RefreshToken.for_user(user)
        serializer = UserSerializer(user)
        return Response({
            "user_data": serializer.data,
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }, status=200)
    except Exception as e:
        return Response({"error":f"unable to login as guest, {e}"}, status=500)


@api_view(["GET"])
def get_user(request, username):
    if not username:
        return Response({"error":"Have not provided proper username"}, status=400)
    
    user = get_user_by_username(username)
    user_stats = get_user_stats(user)

    return Response(user_stats, status=200)
