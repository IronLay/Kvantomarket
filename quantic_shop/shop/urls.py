from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),  # Регистрация
    path('profile/', views.user_profile, name='profile'),  # Профиль пользователя
    path('login/', views.login, name='login'),
    path('confirm_email/', views.confirm_email, name='confirm_email'),
    path('submit_achievement/', views.submit_achievement, name='submit_achievement'),
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/update/', views.update_cart, name='update_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/checkout/', views.checkout, name='checkout'),
    path('orders/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('my-orders/', views.user_orders, name='user_orders'),
]
