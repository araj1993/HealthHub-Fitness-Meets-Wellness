from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, AdminProfile, TrainerProfile


class CommonRegistrationForm(UserCreationForm):
    """Common registration form for all user types"""
    full_name = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter full name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter email'})
    )
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+1234567890'})
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Choose username',
            'autocomplete': 'off'
        }),
        help_text='',
        error_messages={
            'required': 'Username is required.',
            'unique': 'This username is already taken.',
        }
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Enter password',
            'autocomplete': 'new-password'
        }),
        help_text='',
        error_messages={
            'required': 'Password is required.',
        }
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Confirm password',
            'autocomplete': 'new-password'
        }),
        help_text='',
        error_messages={
            'required': 'Please confirm your password.',
        }
    )
    profile_photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = User
        fields = ['full_name', 'email', 'phone_number', 'username', 'password1', 'password2', 'profile_photo']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove all help text from inherited fields
        for fieldname in ['username', 'password1', 'password2']:
            if fieldname in self.fields:
                self.fields[fieldname].help_text = None


class AdminRegistrationForm(forms.ModelForm):
    """Admin-specific fields"""
    qualification = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter qualification'})
    )
    security_pin = forms.CharField(
        max_length=6,
        required=False,
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter 6-digit PIN (optional)'})
    )
    
    class Meta:
        model = AdminProfile
        fields = ['qualification', 'security_pin']


class TrainerRegistrationForm(forms.ModelForm):
    """Trainer-specific fields"""
    qualification = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter qualification'})
    )
    specialization = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Fitness, Yoga, Strength'})
    )
    experience_years = forms.IntegerField(
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Years of experience'})
    )
    certification_details = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List your certifications'})
    )
    licenses = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List your professional licenses (optional)'})
    )
    accreditations = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'List your accreditations (optional)'})
    )
    
    class Meta:
        model = TrainerProfile
        fields = ['qualification', 'specialization', 'experience_years', 'certification_details', 'licenses', 'accreditations']
