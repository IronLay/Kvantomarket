from django.shortcuts import redirect
from django.urls import reverse

class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and not request.user.is_active:
            # Если пользователь аутентифицирован, но не активен
            if request.path != reverse('confirm_email'):  # Исключаем страницу подтверждения
                return redirect('confirm_email')  # Перенаправляем на страницу подтверждения
        return self.get_response(request)