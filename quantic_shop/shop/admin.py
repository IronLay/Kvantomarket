from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, UserProfile

class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profiles'

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    inlines = (UserProfileInline,)
    list_display = ('username', 'email', 'is_kvantum_admin', 'admin_kvantum')
    list_filter = ('is_kvantum_admin', 'admin_kvantum')
    fieldsets = UserAdmin.fieldsets + (
        ('Квантум-администратор', {'fields': ('is_kvantum_admin', 'admin_kvantum')}),
    )

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'kvantum', 'is_approved')
    list_filter = ('kvantum', 'is_approved')