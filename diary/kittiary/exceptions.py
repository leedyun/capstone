from enum import Enum
from rest_framework import status
from rest_framework.exceptions import APIException

class AuthErrorCode(Enum):
    AUTH400_001 = ("Auth400_001", "Invalid authorization code", status.HTTP_400_BAD_REQUEST)
    AUTH401_001 = ("Auth401_001", "Invalid token", status.HTTP_401_UNAUTHORIZED)
    AUTH500_001 = ("Auth500_001", "Internal server error", status.HTTP_500_INTERNAL_SERVER_ERROR)
    AUTH500_002 = ("Auth500_002", "Kakao server error", status.HTTP_500_INTERNAL_SERVER_ERROR)

    def __init__(self, code, message, status_code):
        self.code = code
        self.message = message
        self.status_code = status_code

class AuthException(APIException):
    def __init__(self, error_code: AuthErrorCode):
        self.status_code = error_code.status_code
        self.detail = {
            "errorCode": error_code.code,
            "message": error_code.message
        } 