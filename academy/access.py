from functools import wraps
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from .models import Subject, Resource

def role_required(admin=False):
    def decorator(fn):
        @wraps(fn)
        def wrapped(request,*args,**kwargs):
            u=request.user
            if not u.is_authenticated: return redirect('admin_login' if admin else 'login')
            if not u.is_active: raise PermissionDenied
            if admin and not u.is_superuser: raise PermissionDenied
            if not admin and not u.is_superuser and not hasattr(u,'profile'): raise PermissionDenied
            return fn(request,*args,**kwargs)
        return wrapped
    return decorator

def subjects_for(user):
    qs=Subject.objects.select_related('semester__year')
    return qs if user.is_superuser else qs.filter(semester__year_id=user.profile.year_id)

def resources_for(user):
    qs=Resource.objects.select_related('subject__semester__year')
    return qs if user.is_superuser else qs.filter(approved=True,subject__semester__year_id=user.profile.year_id)
