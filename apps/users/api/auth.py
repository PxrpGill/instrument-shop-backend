from typing import Any, Optional
from ninja.security import HttpBearer
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from apps.users.models import Customer


class CustomerAuth(HttpBearer):
    """Аутентификация для клиентов через JWT токен."""

    def authenticate(self, request: Any) -> Optional[Customer]:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        
        try:
            auth = JWTAuthentication()
            result = auth.authenticate(request)
            if result is None:
                return None
            
            user, validated_token = result
            
            # Проверяем, что это Customer, а не Django User
            if isinstance(user, Customer):
                return user
            
            return None
        except (InvalidToken, AuthenticationFailed):
            return None


class OptionalCustomerAuth(HttpBearer):
    """Необязательная аутентификация для клиентов."""

    def authenticate(self, request: Any) -> Optional[Customer]:
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return None
        
        try:
            auth = JWTAuthentication()
            result = auth.authenticate(request)
            if result is None:
                return None
            
            user, validated_token = result
            
            if isinstance(user, Customer):
                return user
            
            return None
        except (InvalidToken, AuthenticationFailed):
            return None