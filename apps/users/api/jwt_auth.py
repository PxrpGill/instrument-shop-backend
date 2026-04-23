from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken
from apps.users.models import Customer


class CustomerJWTAuthentication(JWTAuthentication):
    """
    JWT аутентификация для клиентов (Customer).
    Ищет пользователя в модели Customer по ID из токена.
    Автоматически кэширует роли в токене для производительности.
    """

    def get_user(self, validated_token: dict) -> Customer:
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
        result = super().authenticate(request)

        if result is not None:
            user, token = result
            # Прикрепляем customer к request для использования в permissions
            request.customer = user

        return result
