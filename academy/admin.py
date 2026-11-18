from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, ActivityLog, PromotionHistory
admin.site.site_header='CLARITY · System administration'
# Domain mutations use validated application forms, not generic admin editing.
admin.site.register(User,UserAdmin)
@admin.register(ActivityLog,PromotionHistory)
class AuditAdmin(admin.ModelAdmin):
    def has_add_permission(self,request): return False
    def has_change_permission(self,request,obj=None): return False
    def has_delete_permission(self,request,obj=None): return False
