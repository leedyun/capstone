from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        logger.debug("Starting authentication process")
        logger.debug(f"Request headers: {request.headers}")
        logger.debug(f"Request cookies: {request.COOKIES}")
        
        # 헤더에서 JWT 토큰 확인
        header = self.get_header(request)
        if header:
            logger.debug("Found Authorization header")
            raw_token = self.get_raw_token(header)
            if raw_token:
                try:
                    validated_token = self.get_validated_token(raw_token)
                    user = self.get_user(validated_token)
                    logger.debug(f"Successfully authenticated user from header: {user.username}")
                    return (user, validated_token)
                except Exception as e:
                    logger.debug(f"Header token validation failed: {str(e)}")

        # 쿠키에서 JWT 토큰 확인
        cookie_name = settings.SIMPLE_JWT['AUTH_COOKIE']
        token = request.COOKIES.get(cookie_name)
        
        if token:
            logger.debug(f"Found token in cookie: {cookie_name}")
            try:
                validated_token = self.get_validated_token(token)
                user = self.get_user(validated_token)
                logger.debug(f"Successfully authenticated user from cookie: {user.username}")
                return (user, validated_token)
            except Exception as e:
                logger.debug(f"Cookie token validation failed: {str(e)}")
        else:
            logger.debug(f"No token found in cookie: {cookie_name}")

        logger.debug("Authentication failed: No valid token found")
        return None

    def authenticate_header(self, request):
        return 'Bearer' 