from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, AdminProfile, TrainerProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'full_name', 'email', 'role', 'date_of_registration', 'is_active']
    list_filter = ['role', 'is_active', 'date_of_registration']
    search_fields = ['username', 'full_name', 'email', 'phone_number']
    ordering = ['-date_of_registration']
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Custom Info', {'fields': ('role', 'full_name', 'phone_number', 'profile_photo', 'date_of_registration')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Custom Info', {'fields': ('role', 'full_name', 'email', 'phone_number', 'profile_photo')}),
    )


@admin.register(AdminProfile)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'qualification']
    search_fields = ['user__full_name', 'qualification']


@admin.register(TrainerProfile)
class TrainerProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'specialization', 'experience_years']
    list_filter = ['specialization']
    search_fields = ['user__full_name', 'specialization', 'certification_details']
