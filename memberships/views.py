from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login
from django.conf import settings
from django.core.mail import EmailMessage
from django.contrib.auth.decorators import login_required
from django.db.models import Avg, Count, Q
from accounts.forms import CommonRegistrationForm
from accounts.models import User
from .forms import UserMembershipForm, L3AddonForm
from .models import UserMembership, L3Addon, PaymentReceipt, TrainerRating
from .utils import generate_membership_receipt
from decimal import Decimal
import os


def send_membership_email(user, membership, pdf_path):
    """Send membership registration confirmation email with PDF receipt"""
    subject = 'Welcome to HealthHub - Membership Registration Successful'
    
    # Get membership tier display name
    tier_names = {
        'L1': 'L1 FitStarter',
        'L2': 'L2 ProActive',
        'L3': 'L3 EliteChamp'
    }
    tier_name = tier_names.get(membership.membership_tier, membership.membership_tier)
    
    # Build addons list
    addons_list = ""
    if membership.membership_tier == 'L3':
        l3_addons = membership.l3_addons.all()
        if l3_addons:
            addons_list = "\n\nL3 Add-ons Selected:"
            for addon in l3_addons:
                addons_list += f"\n  - {addon.get_addon_type_display()}"
                if addon.assigned_trainer:
                    addons_list += f" (Trainer: {addon.assigned_trainer.full_name})"
    
    message = f"""
Dear {user.full_name},

Congratulations! Your HealthHub membership registration is complete.

Membership Details:
- Registration ID: {membership.registration_id}
- Tier: {tier_name}
- Base Fee: ₹{membership.base_registration_fee}
- Monthly Fee: ₹{membership.monthly_fee:.2f}
- Discount: ₹{membership.discount_amount:.2f}
- Add-on Fees: ₹{membership.addon_fees:.2f}
- Total Amount: ₹{membership.total_amount:.2f}
- Registration Date: {membership.date_of_joining.strftime('%B %d, %Y')}
{addons_list}

Your membership receipt is attached to this email for your records.

You can now login to your member dashboard using your username and password.

Login URL: http://127.0.0.1:8000/login/

Thank you for choosing HealthHub. We look forward to helping you achieve your fitness goals!

Best regards,
The HealthHub Team
Where Fitness Meets Wellness
"""
    
    try:
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[user.email]
        )
        
        # Attach PDF receipt
        if os.path.exists(pdf_path):
            email.attach_file(pdf_path)
        
        email.send(fail_silently=False)
    except Exception as e:
        print(f"Error sending email: {e}")


def register_user(request):
    """User registration with membership selection"""
    if request.method == 'POST':
        common_form = CommonRegistrationForm(request.POST, request.FILES)
        membership_form = UserMembershipForm(request.POST)
        addon_form = L3AddonForm(request.POST)
        
        if common_form.is_valid() and membership_form.is_valid():
            # Create user
            user = common_form.save(commit=False)
            user.role = 'USER'
            user.save()
            
            # Create membership
            membership = membership_form.save(commit=False)
            membership.user = user
            
            # Calculate addon fees for L3
            addon_total = Decimal('0')
            if membership.membership_tier == 'L3' and addon_form.is_valid():
                addon_selections = []
                
                if addon_form.cleaned_data.get('personal_trainer'):
                    addon_selections.append('TRAINER')
                    addon_total += Decimal('1000')
                
                if addon_form.cleaned_data.get('zumba_martial_arts'):
                    addon_selections.append('ZUMBA')
                    addon_total += Decimal('1000')
                
                if addon_form.cleaned_data.get('premium_nutrition'):
                    addon_selections.append('NUTRITION')
                    addon_total += Decimal('1000')
                
                if addon_form.cleaned_data.get('mental_wellness'):
                    addon_selections.append('WELLNESS')
                    addon_total += Decimal('1000')
                
                membership.addon_fees = addon_total
            
            # Save membership (this will trigger calculate_total_fee)
            membership.save()
            
            # Create L3 addons if applicable
            if membership.membership_tier == 'L3' and addon_form.is_valid():
                selected_trainer_id = addon_form.cleaned_data.get('selected_trainer')
                assigned_trainer = None
                
                # Get the trainer object if trainer addon is selected
                if 'TRAINER' in addon_selections and selected_trainer_id:
                    try:
                        assigned_trainer = User.objects.get(id=selected_trainer_id, role='TRAINER')
                    except User.DoesNotExist:
                        pass
                
                for addon_type in addon_selections:
                    # Assign trainer only to the TRAINER addon
                    trainer = assigned_trainer if addon_type == 'TRAINER' else None
                    L3Addon.objects.create(
                        membership=membership,
                        addon_type=addon_type,
                        fee=Decimal('1000'),
                        assigned_trainer=trainer
                    )
            
            # Generate PDF receipt
            receipt = PaymentReceipt.objects.create(membership=membership)
            
            # Create receipts directory if it doesn't exist
            receipts_dir = os.path.join(settings.MEDIA_ROOT, 'receipts')
            os.makedirs(receipts_dir, exist_ok=True)
            
            # Generate PDF
            pdf_filename = f'receipt_{membership.registration_id}.pdf'
            pdf_path = os.path.join(receipts_dir, pdf_filename)
            
            try:
                generate_membership_receipt(membership, pdf_path)
                receipt.pdf_file = f'receipts/{pdf_filename}'
                receipt.save()
                
                # Send confirmation email with PDF receipt
                send_membership_email(user, membership, pdf_path)
                
            except Exception as e:
                messages.warning(request, f'Registration successful but PDF generation failed: {str(e)}')
            
            messages.success(request, f'User registration completed successfully! A confirmation email with your membership receipt has been sent to {user.email}. Please login to continue.')
            return redirect('login')
        else:
            # Display form errors
            if not common_form.is_valid():
                for field, errors in common_form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
            if not membership_form.is_valid():
                for field, errors in membership_form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
    else:
        common_form = CommonRegistrationForm()
        membership_form = UserMembershipForm()
        addon_form = L3AddonForm()
    
    return render(request, 'memberships/register_user.html', {
        'common_form': common_form,
        'membership_form': membership_form,
        'addon_form': addon_form,
        'role_title': 'User Registration'
    })


def membership_success(request, membership_id):
    """Success page with receipt download"""
    try:
        membership = UserMembership.objects.select_related('user', 'receipt').prefetch_related('l3_addons').get(id=membership_id)
        return render(request, 'memberships/success.html', {'membership': membership})
    except UserMembership.DoesNotExist:
        messages.error(request, 'Membership not found.')
        return redirect('home')


def fee_calculator_ajax(request):
    """AJAX endpoint for real-time fee calculation"""
    if request.method == 'GET':
        tier = request.GET.get('tier', 'L1')
        months = int(request.GET.get('months', 0))
        pay_advance = request.GET.get('pay_advance') == 'true'
        
        # Calculate fees
        base_fee = 2000
        monthly_rate = 1500 if tier == 'L1' else 2500
        
        monthly_total = 0
        discount = 0
        
        if pay_advance and months > 0:
            monthly_total = monthly_rate * months
            if months > 2:
                discount = 200 * (months - 2)
                monthly_total -= discount
        
        total = base_fee + monthly_total
        
        return render(request, 'memberships/fee_calculator.html', {
            'base_fee': base_fee,
            'monthly_fee': monthly_total,
            'discount': discount,
            'total': total
        })
    
    return redirect('home')


@login_required
def rate_trainer(request, trainer_id):
    """Allow L3 users to rate their assigned trainer"""
    if request.user.role != 'USER':
        messages.error(request, 'Only members can rate trainers.')
        return redirect('user_dashboard')
    
    # Check if user has L3 membership
    try:
        membership = UserMembership.objects.get(user=request.user, membership_tier='L3')
    except UserMembership.DoesNotExist:
        messages.error(request, 'Only L3 Elite Champion members can rate trainers.')
        return redirect('user_dashboard')
    
    # Verify the trainer exists and is assigned to this user
    try:
        trainer = User.objects.get(id=trainer_id, role='TRAINER')
        # Check if trainer is assigned to user through L3 addon
        assigned = L3Addon.objects.filter(
            membership=membership, 
            assigned_trainer=trainer, 
            addon_type='TRAINER'
        ).exists()
        
        if not assigned:
            messages.error(request, 'You can only rate trainers assigned to you.')
            return redirect('user_dashboard')
    except User.DoesNotExist:
        messages.error(request, 'Trainer not found.')
        return redirect('user_dashboard')
    
    if request.method == 'POST':
        rating = request.POST.get('rating')
        review = request.POST.get('review', '')
        
        if not rating or int(rating) not in [1, 2, 3, 4, 5]:
            messages.error(request, 'Please select a valid rating (1-5 stars).')
            return redirect('rate_trainer', trainer_id=trainer_id)
        
        # Create or update rating
        trainer_rating, created = TrainerRating.objects.update_or_create(
            user=request.user,
            trainer=trainer,
            membership=membership,
            defaults={
                'rating': int(rating),
                'review': review
            }
        )
        
        if created:
            messages.success(request, f'Your rating for {trainer.full_name} has been submitted successfully!')
        else:
            messages.success(request, f'Your rating for {trainer.full_name} has been updated successfully!')
        
        return redirect('user_dashboard')
    
    # Check if user already rated this trainer
    existing_rating = TrainerRating.objects.filter(
        user=request.user,
        trainer=trainer,
        membership=membership
    ).first()
    
    context = {
        'trainer': trainer,
        'existing_rating': existing_rating
    }
    return render(request, 'memberships/rate_trainer.html', context)


@login_required
def trainer_ratings(request, trainer_id):
    """View all ratings for a specific trainer"""
    try:
        trainer = User.objects.get(id=trainer_id, role='TRAINER')
    except User.DoesNotExist:
        messages.error(request, 'Trainer not found.')
        return redirect('approved_trainers')
    
    ratings = TrainerRating.objects.filter(trainer=trainer).select_related('user', 'membership')
    
    # Calculate average rating
    avg_rating = ratings.aggregate(Avg('rating'))['rating__avg'] or 0
    total_ratings = ratings.count()
    
    # Rating distribution with percentages
    rating_distribution = []
    for stars in [5, 4, 3, 2, 1]:
        count = ratings.filter(rating=stars).count()
        percentage = (count * 100 / total_ratings) if total_ratings > 0 else 0
        rating_distribution.append({
            'stars': stars,
            'count': count,
            'percentage': round(percentage, 1)
        })
    
    context = {
        'trainer': trainer,
        'ratings': ratings,
        'avg_rating': round(avg_rating, 1),
        'total_ratings': total_ratings,
        'rating_distribution': rating_distribution
    }
    return render(request, 'memberships/trainer_ratings.html', context)


