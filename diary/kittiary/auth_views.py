from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from allauth.socialaccount.models import SocialAccount
from allauth.socialaccount.providers.kakao.views import KakaoOAuth2Adapter
from allauth.socialaccount.providers.oauth2.client import OAuth2Client
from dj_rest_auth.registration.views import SocialLoginView
from .serializers import UserSerializer
import requests

User = get_user_model()

KAKAO_TOKEN_API = "https://kauth.kakao.com/oauth/token"
KAKAO_USER_API = "https://kapi.kakao.com/v2/user/me"
CLIENT_ID = "6242b32743c06796acdfd168cd435126"  # REST API 키
REDIRECT_URI = "https://localhost:8000/oauth/kakao/callback"

class KakaoLogin(SocialLoginView):
    adapter_class = KakaoOAuth2Adapter
    client_class = OAuth2Client
    callback_url = "https://localhost:8000/oauth/kakao/callback"

    def get_response(self):
        response = super().get_response()
        if self.user:
            response.data['user'] = UserSerializer(self.user).data
        return response

@api_view(['POST'])
@permission_classes([AllowAny])
def kakao_callback(request):
    code = request.data.get('code')
    if not code:
        return Response({'error': 'Kakao OAuth code is required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # 카카오 토큰 받기
        token_response = requests.post(
            KAKAO_TOKEN_API,
            data={
                'grant_type': 'authorization_code',
                'client_id': CLIENT_ID,
                'redirect_uri': REDIRECT_URI,
                'code': code,
            }
        )
        token_response.raise_for_status()
        access_token = token_response.json().get('access_token')

        # 카카오 사용자 정보 받기
        user_response = requests.get(
            KAKAO_USER_API,
            headers={'Authorization': f'Bearer {access_token}'}
        )
        user_response.raise_for_status()
        user_data = user_response.json()
        
        # 카카오 ID로 유저 찾기 또는 생성
        kakao_id = str(user_data.get('id'))
        kakao_account = user_data.get('kakao_account', {})
        
        try:
            user = User.objects.get(social_login_id=kakao_id)
        except User.DoesNotExist:
            # 새 유저 생성
            nickname = user_data.get('properties', {}).get('nickname', f'user_{kakao_id}')
            email = kakao_account.get('email')
            
            user = User.objects.create_user(
                username=nickname,
                email=email,
                social_login_id=kakao_id
            )

        # JWT 토큰 생성
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })
        
    except requests.RequestException as e:
        return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
def refresh_token(request):
    refresh_token = request.data.get('refresh')
    if not refresh_token:
        return Response({'error': 'Refresh token is required'}, 
                       status=status.HTTP_400_BAD_REQUEST)
    
    try:
        refresh = RefreshToken(refresh_token)
        return Response({
            'access': str(refresh.access_token)
        })
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def logout(request):
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        return Response(status=status.HTTP_204_NO_CONTENT)
    except Exception:
        return Response(status=status.HTTP_204_NO_CONTENT) 