from django.contrib import admin


from .models import UserProfile
# Create your views here.

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('username', 'role', 'department', 'active_status', 'created_at')
    list_filter = ('role', 'department', 'active_status')