"""
JWT Authentication for Customer model.
"""
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, AuthenticationFailed
from rest_framework_simplejwt.settings import api_settings
from apps.users.models import Customer


class CustomerJWTAuthentication(JWTAuthentication):
    """
    JWT аутентификация для клиентов (Customer).
    Ищет пользователя в модели Customer по ID из токена.
    Автоматически кэширует роли в токене для производительности.
    """

    def get_user(self, validated_token):
        """
        Получение пользователя из токена с предзагрузкой ролей.
        """
        user_id = validated_token.get('user_id')
        
        if not user_id:
            raise InvalidToken('Токен не содержит user_id')
        
        try:
            # Получаем клиента с предзагрузкой ролей
            customer = Customer.objects.prefetch_related('roles').get(
                id=user_id,
                is_active=True
            )
        except Customer.DoesNotExist:
            raise InvalidToken('Пользователь не найден')
        
        if not customer.is_active:
            raise InvalidToken('Пользователь неактивен')
        
        # Прикрепляем роли к объекту для кэширования (если еще не загружены)
        if not hasattr(customer, '_prefetched_objects_cache') or 'roles' not in getattr(customer, '_prefetched_objects_cache', {}):
            # Если роли не были prefetched, загружаем их
            customer.roles.all()
        
        return customer

    def authenticate(self, request):
        """
        Расширенная аутентификация, которая добавляет роли в request.
        """
        try:
            # Получаем заголовок Authorization
            header = self.get_header(request)
            if header is None:
                return None
            
            raw_token = self.get_raw_token(header)
            if raw_token is None:
                return None
            
            # Валидируем токен
            validated_token = self.get_validated_token(raw_token)
            
            # Получаем пользователя
            user = self.get_user(validated_token)
            
            # Прикрепляем customer к request для использования в permissions
            request.customer = user
            
            return (user, validated_token)
            
        except InvalidToken as e:
            raise AuthenticationFailed(str(e))
        except Exception as e:
            # Логируем ошибку, но не падаем
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Authentication error: {e}")
            return None
