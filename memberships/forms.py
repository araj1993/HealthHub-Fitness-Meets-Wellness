from django import forms
from .models import UserMembership, L3Addon


class UserMembershipForm(forms.ModelForm):
    """Form for user membership registration"""
    
    MEMBERSHIP_CHOICES = [
        ('L1', 'L1 – FitStarter'),
        ('L2', 'L2 – ProActive'),
        ('L3', 'L3 – EliteChamp'),
    ]
    
    membership_tier = forms.ChoiceField(
        choices=MEMBERSHIP_CHOICES,
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'}),
        label='Select Membership Type'
    )
    
    age = forms.IntegerField(
        min_value=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter age'})
    )
    
    current_weight = forms.DecimalField(
        max_digits=5,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Weight in kg'})
    )
    
    date_of_joining = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    )
    
    medical_history = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter medical history (if any)'})
    )
    
    pay_monthly_in_advance = forms.BooleanField(
        required=False,
        label='Pay monthly fee in advance?',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    months_selected = forms.IntegerField(
        required=False,
        min_value=1,
        initial=1,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Select number of months'})
    )
    
    # L2 Specific
    extra_protein_needed = forms.BooleanField(
        required=False,
        label='Is extra protein supplementation needed?',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = UserMembership
        fields = [
            'membership_tier', 'age', 'current_weight', 'date_of_joining',
            'medical_history', 'pay_monthly_in_advance', 'months_selected',
            'extra_protein_needed'
        ]
    
    def clean(self):
        cleaned_data = super().clean()
        pay_monthly = cleaned_data.get('pay_monthly_in_advance')
        months = cleaned_data.get('months_selected')
        
        if pay_monthly and (not months or months < 1):
            raise forms.ValidationError('Please select number of months if paying in advance.')
        
        return cleaned_data


class L3AddonForm(forms.Form):
    """Form for L3 Elite Champion add-ons"""
    
    personal_trainer = forms.BooleanField(
        required=False,
        label='Personal Trainer Booking (₹1000)',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_personal_trainer'})
    )
    
    selected_trainer = forms.ChoiceField(
        required=False,
        label='Select Your Trainer',
        widget=forms.Select(attrs={'class': 'form-select', 'id': 'id_selected_trainer'})
    )
    
    zumba_martial_arts = forms.BooleanField(
        required=False,
        label='Zumba & Martial Arts (Live/Recorded) (₹1000)',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    premium_nutrition = forms.BooleanField(
        required=False,
        label='Premium Nutrition Hub (drinks + meals) (₹1000)',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    mental_wellness = forms.BooleanField(
        required=False,
        label='Mental Wellness Dashboard (₹1000)',
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate trainer choices
        from accounts.models import User
        trainers = User.objects.filter(role='TRAINER', is_active=True).select_related('trainer_profile')
        trainer_choices = [('', '-- Select a Trainer --')]
        for trainer in trainers:
            profile = getattr(trainer, 'trainer_profile', None)
            if profile:
                label = f"{trainer.full_name} - {profile.specialization} ({profile.experience_years} years exp.)"
            else:
                label = trainer.full_name
            trainer_choices.append((trainer.id, label))
        self.fields['selected_trainer'].choices = trainer_choices
