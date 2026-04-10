from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from apps.users.models import Customer


class CustomerJWTAuthentication(JWTAuthentication):
    """
    JWT аутентификация для клиентов (Customer).
    Ищет пользователя в модели Customer по ID из токена.
    """

    def get_user(self, validated_token: dict) -> Customer:
        """Получение пользователя из токена."""
        user_id = validated_token.get('user_id')
        
        if not user_id:
            raise InvalidToken('Токен не содержит user_id')
        
        try:
            customer = Customer.objects.get(id=user_id, is_active=True)
        except Customer.DoesNotExist:
            raise InvalidToken('Пользователь не найден')
        
        if not customer.is_active:
            raise InvalidToken('Пользователь неактивен')
        
        return customer