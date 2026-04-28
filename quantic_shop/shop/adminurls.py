from django.urls import path
from . import views

urlpatterns = [
    path('products/', views.product_list, name='product_list'),
    path('products/add/', views.add_product, name='add_product'),
    path('products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('products/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('approve-profiles/', views.admin_approve_profiles, name='admin_approve_profiles'),
    path('approve-profile/<int:profile_id>/', views.admin_approve_profile, name='admin_approve_profile'),
    path('delete-profile/<int:profile_id>/', views.admin_delete_profile, name='admin_delete_profile'),
    path('review-achievements/', views.review_achievements, name='review_achievements'),
    path('achievements/review/<int:pk>/', views.review_achievement_detail, name='review_achievement_detail'),
    path('orders/<int:order_id>/', views.order_admin_detail, name='order_admin_detail'),
    path('orders/<int:order_id>/', views.order_admin_detail, name='order_admin_detail'),
]
