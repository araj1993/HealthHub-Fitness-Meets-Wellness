from django.contrib import admin
from .models import (
    UserMembership, L3Addon, PaymentReceipt, WorkoutPlan, 
    Exercise, ProteinIntake, MedicalCheckup, TrainerRating
)


class L3AddonInline(admin.TabularInline):
    model = L3Addon
    extra = 0


@admin.register(UserMembership)
class UserMembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'membership_tier', 'registration_id', 'total_amount', 'created_at']
    list_filter = ['membership_tier', 'pay_monthly_in_advance', 'created_at']
    search_fields = ['user__full_name', 'registration_id']
    readonly_fields = ['registration_id', 'total_amount', 'discount_amount', 'created_at', 'updated_at']
    inlines = [L3AddonInline]
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'membership_tier', 'registration_id')
        }),
        ('Health Details', {
            'fields': ('age', 'current_weight', 'date_of_joining', 'medical_history')
        }),
        ('Payment Details', {
            'fields': ('pay_monthly_in_advance', 'months_selected', 'extra_protein_needed')
        }),
        ('Fee Breakdown', {
            'fields': ('base_registration_fee', 'monthly_fee', 'discount_amount', 'addon_fees', 'total_amount')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(L3Addon)
class L3AddonAdmin(admin.ModelAdmin):
    list_display = ['membership', 'addon_type', 'fee']
    list_filter = ['addon_type']


@admin.register(PaymentReceipt)
class PaymentReceiptAdmin(admin.ModelAdmin):
    list_display = ['receipt_number', 'membership', 'generated_at']
    readonly_fields = ['receipt_number', 'generated_at']
    search_fields = ['receipt_number', 'membership__user__full_name']


class ExerciseInline(admin.TabularInline):
    model = Exercise
    extra = 0
    fields = ['exercise_name', 'exercise_type', 'sets', 'reps', 'order', 'is_completed']


@admin.register(WorkoutPlan)
class WorkoutPlanAdmin(admin.ModelAdmin):
    list_display = ['membership', 'week_number', 'day_of_week', 'start_date', 'end_date', 'is_active']
    list_filter = ['day_of_week', 'is_active', 'week_number']
    search_fields = ['membership__user__full_name']
    inlines = [ExerciseInline]
    date_hierarchy = 'start_date'


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ['exercise_name', 'workout_plan', 'exercise_type', 'sets', 'reps', 'is_completed']
    list_filter = ['exercise_type', 'is_completed']
    search_fields = ['exercise_name', 'workout_plan__membership__user__full_name']


@admin.register(ProteinIntake)
class ProteinIntakeAdmin(admin.ModelAdmin):
    list_display = ['membership', 'date', 'morning_intake', 'evening_intake', 'updated_by_admin']
    list_filter = ['morning_intake', 'evening_intake', 'date']
    search_fields = ['membership__user__full_name']
    date_hierarchy = 'date'
    readonly_fields = ['created_at', 'updated_at']


@admin.register(MedicalCheckup)
class MedicalCheckupAdmin(admin.ModelAdmin):
    list_display = ['membership', 'checkup_date', 'checkup_type', 'status', 'next_checkup_date']
    list_filter = ['status', 'checkup_date']
    search_fields = ['membership__user__full_name', 'checkup_type', 'conducted_by']
    date_hierarchy = 'checkup_date'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Checkup Information', {
            'fields': ('membership', 'checkup_date', 'checkup_type', 'status')
        }),
        ('Medical Details', {
            'fields': ('conducted_by', 'findings', 'recommendations', 'next_checkup_date')
        }),
        ('Admin Details', {
            'fields': ('updated_by_admin', 'created_at', 'updated_at')
        }),
    )


@admin.register(TrainerRating)
class TrainerRatingAdmin(admin.ModelAdmin):
    list_display = ['user', 'trainer', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']
    search_fields = ['user__full_name', 'trainer__full_name', 'review']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Rating Information', {
            'fields': ('user', 'trainer', 'membership', 'rating')
        }),
        ('Review', {
            'fields': ('review',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
