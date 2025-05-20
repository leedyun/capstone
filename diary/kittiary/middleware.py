from django.conf import settings
from rest_framework_simplejwt.authentication import JWTAuthentication
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

class JWTAuthenticationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.jwt_authentication = JWTAuthentication()

    def __call__(self, request):
        self._authenticate(request)
        return self.get_response(request)

    def _authenticate(self, request):
        User = get_user_model()
        authorization_cookie = request.COOKIES.get(settings.SIMPLE_JWT['AUTH_COOKIE'])
        
        if not authorization_cookie:
            return None

        try:
            validated_token = self.jwt_authentication.get_validated_token(authorization_cookie)
            user = self.jwt_authentication.get_user(validated_token)
            request.user = user
        except (InvalidToken, TokenError):
            pass 