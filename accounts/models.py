from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import RegexValidator
import uuid

# Custom User Model with role-based authentication
class User(AbstractUser):
    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('USER', 'User'),
        ('TRAINER', 'Trainer'),
    ]
    
    # Common fields for all users
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    full_name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be valid")]
    )
    date_of_registration = models.DateTimeField(auto_now_add=True)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    
    # For tracking
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-date_of_registration']
    
    def __str__(self):
        return f"{self.full_name} ({self.role})"


class AdminProfile(models.Model):
    """Extended profile for Admin users"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    qualification = models.CharField(max_length=255)
    security_pin = models.CharField(max_length=6, blank=True, null=True)
    
    class Meta:
        verbose_name = 'Admin Profile'
        verbose_name_plural = 'Admin Profiles'
    
    def __str__(self):
        return f"Admin: {self.user.full_name}"


class TrainerProfile(models.Model):
    """Extended profile for Trainer users"""
    APPROVAL_STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='trainer_profile')
    qualification = models.CharField(max_length=255)
    specialization = models.CharField(max_length=255, help_text="e.g., Fitness, Yoga, Strength")
    experience_years = models.PositiveIntegerField(help_text="Years of experience")
    certification_details = models.TextField()
    licenses = models.TextField(help_text="Professional licenses held", blank=True)
    accreditations = models.TextField(help_text="Professional accreditations", blank=True)
    
    # Approval fields
    approval_status = models.CharField(
        max_length=10, 
        choices=APPROVAL_STATUS_CHOICES, 
        default='PENDING',
        help_text="Admin approval status"
    )
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_trainers',
        limit_choices_to={'role': 'ADMIN'}
    )
    approval_date = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True, help_text="Reason for rejection (if applicable)")
    
    class Meta:
        verbose_name = 'Trainer Profile'
        verbose_name_plural = 'Trainer Profiles'
    
    def __str__(self):
        return f"Trainer: {self.user.full_name} - {self.specialization} ({self.approval_status})"
