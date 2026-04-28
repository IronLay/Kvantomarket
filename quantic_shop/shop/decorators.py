from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied

def kvantum_admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_kvantum_admin:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper


def approved_user(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if not hasattr(request.user, 'userprofile') or not request.user.userprofile.is_approved:
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return wrapper