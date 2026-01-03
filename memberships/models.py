from django.db import models
from accounts.models import User
import uuid
from decimal import Decimal


class UserMembership(models.Model):
    """User membership with tier selection"""
    MEMBERSHIP_TIERS = [
        ('L1', 'FitStarter'),
        ('L2', 'ProActive'),
        ('L3', 'EliteChamp'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending Payment'),
        ('PAID', 'Payment Confirmed'),
        ('CANCELLED', 'Payment Cancelled'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='membership')
    membership_tier = models.CharField(max_length=2, choices=MEMBERSHIP_TIERS)
    registration_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    # Common User fields
    age = models.PositiveIntegerField()
    current_weight = models.DecimalField(max_digits=5, decimal_places=2, help_text="Weight in kg")
    date_of_joining = models.DateField()
    medical_history = models.TextField(blank=True, null=True)
    
    # Payment details
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    payment_confirmed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='confirmed_payments')
    payment_confirmed_date = models.DateTimeField(null=True, blank=True)
    payment_notes = models.TextField(blank=True, null=True, help_text="Admin notes about payment")
    pay_monthly_in_advance = models.BooleanField(default=False)
    months_selected = models.PositiveIntegerField(default=0, help_text="Number of months paid in advance")
    
    # L2 specific
    extra_protein_needed = models.BooleanField(default=False, help_text="L2: Extra protein supplementation")
    
    # Fee calculation
    base_registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=2000)
    monthly_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    addon_fees = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'User Membership'
        verbose_name_plural = 'User Memberships'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.full_name} - {self.get_membership_tier_display()}"
    
    def calculate_total_fee(self):
        """Calculate total fee based on tier and selections"""
        # Base registration fee
        total = Decimal(self.base_registration_fee)
        
        # Monthly fee based on tier
        if self.membership_tier == 'L1':
            monthly_rate = Decimal('1500')
        elif self.membership_tier == 'L2':
            monthly_rate = Decimal('2500')
        elif self.membership_tier == 'L3':
            monthly_rate = Decimal('2500')
        else:
            monthly_rate = Decimal('0')
        
        # Calculate monthly payment
        if self.pay_monthly_in_advance and self.months_selected > 0:
            monthly_total = monthly_rate * self.months_selected
            
            # Apply discount for months > 2
            if self.months_selected > 2:
                discount_months = self.months_selected - 2
                discount = Decimal('200') * discount_months
                self.discount_amount = discount
                monthly_total -= discount
            
            self.monthly_fee = monthly_total
            total += monthly_total
        
        # Add addon fees (for L3)
        total += Decimal(self.addon_fees)
        
        self.total_amount = total
        return total
    
    def get_membership_expiry_date(self):
        """Calculate membership expiry date based on months selected"""
        if self.pay_monthly_in_advance and self.months_selected > 0:
            from dateutil.relativedelta import relativedelta
            return self.date_of_joining + relativedelta(months=self.months_selected)
        return None
    
    def is_expiring_soon(self):
        """Check if membership expires within 7 days"""
        expiry_date = self.get_membership_expiry_date()
        if expiry_date:
            from django.utils import timezone
            days_until_expiry = (expiry_date - timezone.now().date()).days
            return 0 <= days_until_expiry <= 7
        return False
    
    def days_until_expiry(self):
        """Get number of days until membership expires"""
        expiry_date = self.get_membership_expiry_date()
        if expiry_date:
            from django.utils import timezone
            return (expiry_date - timezone.now().date()).days
        return None
    
    def save(self, *args, **kwargs):
        self.calculate_total_fee()
        super().save(*args, **kwargs)


class L3Addon(models.Model):
    """Add-ons for L3 Elite Champion tier"""
    ADDON_CHOICES = [
        ('TRAINER', 'Personal Trainer Booking'),
        ('ZUMBA', 'Zumba & Martial Arts (Live/Recorded)'),
        ('NUTRITION', 'Premium Nutrition Hub (drinks + meals)'),
        ('WELLNESS', 'Mental Wellness Dashboard'),
    ]
    
    membership = models.ForeignKey(UserMembership, on_delete=models.CASCADE, related_name='l3_addons')
    addon_type = models.CharField(max_length=20, choices=ADDON_CHOICES)
    fee = models.DecimalField(max_digits=10, decimal_places=2, default=1000)
    assigned_trainer = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, blank=True, 
                                         related_name='assigned_clients', limit_choices_to={'role': 'TRAINER'})
    
    class Meta:
        verbose_name = 'L3 Add-on'
        verbose_name_plural = 'L3 Add-ons'
        unique_together = ['membership', 'addon_type']
    
    def __str__(self):
        return f"{self.membership.user.full_name} - {self.get_addon_type_display()}"


class PaymentReceipt(models.Model):
    """Payment receipt for user memberships"""
    membership = models.OneToOneField(UserMembership, on_delete=models.CASCADE, related_name='receipt')
    receipt_number = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    pdf_file = models.FileField(upload_to='receipts/', blank=True, null=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Payment Receipt'
        verbose_name_plural = 'Payment Receipts'
    
    def __str__(self):
        return f"Receipt #{self.receipt_number} - {self.membership.user.full_name}"


class WorkoutPlan(models.Model):
    """Weekly workout plan for L2 users - AI generated"""
    DAYS_OF_WEEK = [
        ('MON', 'Monday'),
        ('TUE', 'Tuesday'),
        ('WED', 'Wednesday'),
        ('THU', 'Thursday'),
        ('FRI', 'Friday'),
        ('SAT', 'Saturday'),
    ]
    
    membership = models.ForeignKey(UserMembership, on_delete=models.CASCADE, related_name='workout_plans')
    week_number = models.PositiveIntegerField(help_text="Week number since joining")
    day_of_week = models.CharField(max_length=3, choices=DAYS_OF_WEEK)
    start_date = models.DateField(help_text="Start date of this week")
    end_date = models.DateField(help_text="End date of this week")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Workout Plan'
        verbose_name_plural = 'Workout Plans'
        ordering = ['week_number', 'day_of_week']
        unique_together = ['membership', 'week_number', 'day_of_week']
    
    def __str__(self):
        return f"{self.membership.user.full_name} - Week {self.week_number} - {self.get_day_of_week_display()}"


class Exercise(models.Model):
    """Individual exercises in a workout plan"""
    EXERCISE_TYPES = [
        ('CARDIO', 'Cardio'),
        ('STRENGTH', 'Strength Training'),
        ('FLEXIBILITY', 'Flexibility'),
        ('HIIT', 'High Intensity Interval Training'),
        ('YOGA', 'Yoga'),
        ('CORE', 'Core Training'),
    ]
    
    workout_plan = models.ForeignKey(WorkoutPlan, on_delete=models.CASCADE, related_name='exercises')
    exercise_name = models.CharField(max_length=200)
    exercise_type = models.CharField(max_length=20, choices=EXERCISE_TYPES)
    sets = models.PositiveIntegerField(default=1)
    reps = models.PositiveIntegerField(default=1, help_text="Repetitions or duration in minutes")
    description = models.TextField(blank=True, help_text="Exercise instructions")
    order = models.PositiveIntegerField(default=0, help_text="Order of exercise in the plan")
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Exercise'
        verbose_name_plural = 'Exercises'
        ordering = ['workout_plan', 'order']
    
    def __str__(self):
        return f"{self.exercise_name} - {self.workout_plan}"


class ProteinIntake(models.Model):
    """Daily protein intake tracking for L2 users with extra protein option"""
    membership = models.ForeignKey(UserMembership, on_delete=models.CASCADE, related_name='protein_intakes')
    date = models.DateField()
    morning_intake = models.BooleanField(default=False, help_text="Morning protein shake taken")
    evening_intake = models.BooleanField(default=False, help_text="Evening protein shake taken")
    notes = models.TextField(blank=True, help_text="Additional notes from admin")
    updated_by_admin = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, 
                                         related_name='protein_updates', limit_choices_to={'role': 'ADMIN'})
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Protein Intake'
        verbose_name_plural = 'Protein Intakes'
        ordering = ['-date']
        unique_together = ['membership', 'date']
    
    def __str__(self):
        return f"{self.membership.user.full_name} - {self.date}"


class MedicalCheckup(models.Model):
    """Medical checkup records for users with medical conditions"""
    CHECKUP_STATUS = [
        ('SCHEDULED', 'Scheduled'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    membership = models.ForeignKey(UserMembership, on_delete=models.CASCADE, related_name='medical_checkups')
    checkup_date = models.DateField()
    checkup_type = models.CharField(max_length=200, help_text="Type of checkup (e.g., General, Blood Test, etc.)")
    status = models.CharField(max_length=20, choices=CHECKUP_STATUS, default='SCHEDULED')
    findings = models.TextField(blank=True, help_text="Medical findings from the checkup")
    recommendations = models.TextField(blank=True, help_text="Doctor's recommendations")
    next_checkup_date = models.DateField(null=True, blank=True)
    conducted_by = models.CharField(max_length=200, blank=True, help_text="Doctor/Medical professional name")
    updated_by_admin = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, 
                                         related_name='checkup_updates', limit_choices_to={'role': 'ADMIN'})
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Medical Checkup'
        verbose_name_plural = 'Medical Checkups'
        ordering = ['-checkup_date']
    
    def __str__(self):
        return f"{self.membership.user.full_name} - {self.checkup_type} on {self.checkup_date}"


class TrainerRating(models.Model):
    """Ratings and reviews for trainers by L3 users"""
    RATING_CHOICES = [
        (1, '1 - Poor'),
        (2, '2 - Fair'),
        (3, '3 - Good'),
        (4, '4 - Very Good'),
        (5, '5 - Excellent'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trainer_ratings')
    trainer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings', 
                                limit_choices_to={'role': 'TRAINER'})
    membership = models.ForeignKey(UserMembership, on_delete=models.CASCADE, related_name='trainer_ratings')
    rating = models.PositiveIntegerField(choices=RATING_CHOICES)
    review = models.TextField(blank=True, help_text="Optional review comment")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Trainer Rating'
        verbose_name_plural = 'Trainer Ratings'
        ordering = ['-created_at']
        unique_together = ['user', 'trainer', 'membership']
    
    def __str__(self):
        return f"{self.user.full_name} rated {self.trainer.full_name} - {self.rating} stars"
