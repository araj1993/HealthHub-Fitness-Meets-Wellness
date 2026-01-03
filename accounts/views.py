from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone
from django.db.models import Avg, Count
from datetime import timedelta, datetime
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .forms import CommonRegistrationForm, AdminRegistrationForm, TrainerRegistrationForm
from .models import User, AdminProfile, TrainerProfile
from memberships.models import (
    UserMembership, WorkoutPlan, Exercise, ProteinIntake, MedicalCheckup
)


def send_registration_email(user, role):
    """Send registration confirmation email to user"""
    subject = f'Welcome to HealthHub - {role} Registration Successful'
    message = f"""
Dear {user.full_name},

Thank you for registering with HealthHub!

Your {role} account has been successfully created.

Registration Details:
- Full Name: {user.full_name}
- Username: {user.username}
- Email: {user.email}
- Phone: {user.phone_number}
- Role: {role}
- Registration Date: {user.date_of_registration.strftime('%B %d, %Y')}

You can now login to your dashboard using your username and password.

Login URL: http://127.0.0.1:8000/login/

If you have any questions or need assistance, please don't hesitate to contact us.

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
        email.send(fail_silently=False)
    except Exception as e:
        print(f"Error sending email: {e}")


def landing_page(request):
    """Main landing page with links to registration and login"""
    return render(request, 'accounts/landing_page.html')


def home(request):
    """Home page with role selection for registration"""
    # Check if admin already exists
    admin_exists = User.objects.filter(role='ADMIN').exists()
    
    return render(request, 'accounts/home.html', {
        'admin_exists': admin_exists
    })


def register_admin(request):
    """Admin registration view - disabled after first admin is registered"""
    # Check if an admin already exists
    existing_admin = User.objects.filter(role='ADMIN').first()
    
    if existing_admin:
        messages.error(request, 'Admin registration is disabled. An administrator account already exists. Please contact the existing administrator for access.')
        return redirect('login')
    
    if request.method == 'POST':
        common_form = CommonRegistrationForm(request.POST, request.FILES)
        admin_form = AdminRegistrationForm(request.POST)
        
        if common_form.is_valid() and admin_form.is_valid():
            # Double-check no admin was created during form processing
            if User.objects.filter(role='ADMIN').exists():
                messages.error(request, 'Admin registration is disabled. An administrator account already exists.')
                return redirect('login')
            
            # Create user
            user = common_form.save(commit=False)
            user.role = 'ADMIN'
            user.save()
            
            # Create admin profile
            admin_profile = admin_form.save(commit=False)
            admin_profile.user = user
            admin_profile.save()
            
            # Send registration confirmation email
            send_registration_email(user, 'Admin')
            
            messages.success(request, 'Admin registration completed successfully! A confirmation email has been sent to your registered email address. Please login to continue.')
            return redirect('login')
    else:
        common_form = CommonRegistrationForm()
        admin_form = AdminRegistrationForm()
    
    return render(request, 'accounts/register_admin.html', {
        'common_form': common_form,
        'admin_form': admin_form,
        'role_title': 'Admin Registration'
    })


def register_trainer(request):
    """Trainer registration view - requires admin approval"""
    if request.method == 'POST':
        common_form = CommonRegistrationForm(request.POST, request.FILES)
        trainer_form = TrainerRegistrationForm(request.POST)
        
        if common_form.is_valid() and trainer_form.is_valid():
            # Create user (inactive until approved)
            user = common_form.save(commit=False)
            user.role = 'TRAINER'
            user.is_active = False  # Trainer cannot login until approved
            user.save()
            
            # Create trainer profile with pending status
            trainer_profile = trainer_form.save(commit=False)
            trainer_profile.user = user
            trainer_profile.approval_status = 'PENDING'
            trainer_profile.save()
            
            # Send registration confirmation email
            send_registration_email(user, 'Trainer')
            
            messages.success(request, 'Trainer registration completed successfully! Your application is pending admin approval. You will receive an email once your account is reviewed.')
            return redirect('landing_page')
        else:
            # Display form errors
            if not common_form.is_valid():
                for field, errors in common_form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
            if not trainer_form.is_valid():
                for field, errors in trainer_form.errors.items():
                    for error in errors:
                        messages.error(request, f'{field}: {error}')
    else:
        common_form = CommonRegistrationForm()
        trainer_form = TrainerRegistrationForm()
    
    return render(request, 'accounts/register_trainer.html', {
        'common_form': common_form,
        'trainer_form': trainer_form,
        'role_title': 'Trainer Registration'
    })


def user_login(request):
    """Login view for all user types"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Check if trainer is approved
            if user.role == 'TRAINER':
                try:
                    trainer_profile = TrainerProfile.objects.get(user=user)
                    if trainer_profile.approval_status == 'PENDING':
                        messages.warning(request, 'Your trainer account is pending admin approval. Please wait for approval to login.')
                        return render(request, 'accounts/login.html')
                    elif trainer_profile.approval_status == 'REJECTED':
                        messages.error(request, f'Your trainer account has been rejected. Reason: {trainer_profile.rejection_reason}')
                        return render(request, 'accounts/login.html')
                except TrainerProfile.DoesNotExist:
                    messages.error(request, 'Trainer profile not found. Please contact support.')
                    return render(request, 'accounts/login.html')
            
            login(request, user)
            messages.success(request, f'Welcome back, {user.full_name}!')
            
            # Redirect based on role
            if user.role == 'ADMIN':
                return redirect('admin_dashboard')
            elif user.role == 'TRAINER':
                return redirect('trainer_dashboard')
            elif user.role == 'USER':
                return redirect('user_dashboard')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'accounts/login.html')


def user_logout(request):
    """Logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('landing_page')


@login_required
def admin_dashboard(request):
    """Admin dashboard - view all users and their information"""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('landing_page')
    
    all_users = User.objects.all().select_related('admin_profile', 'trainer_profile', 'membership').order_by('-date_of_registration')
    memberships = UserMembership.objects.filter(user__role='USER').select_related('user').prefetch_related('l3_addons')
    
    # Get pending trainer requests
    pending_trainers = TrainerProfile.objects.filter(approval_status='PENDING').select_related('user').order_by('-user__date_of_registration')
    
    # Count memberships expiring within 7 days
    expiring_soon_count = sum(1 for m in memberships if m.is_expiring_soon())
    
    # Count memberships by tier
    l1_count = memberships.filter(membership_tier='L1').count()
    l2_count = memberships.filter(membership_tier='L2').count()
    l3_count = memberships.filter(membership_tier='L3').count()
    
    # Count pending payments
    pending_payments_count = memberships.filter(payment_status='PENDING').count()
    
    context = {
        'all_users': all_users,
        'memberships': memberships,
        'pending_trainers': pending_trainers,
        'pending_trainers_count': pending_trainers.count(),
        'pending_payments_count': pending_payments_count,
        'total_users': all_users.filter(role='USER').count(),
        'total_trainers': all_users.filter(role='TRAINER', trainer_profile__approval_status='APPROVED').count(),
        'total_admins': all_users.filter(role='ADMIN').count(),
        'expiring_soon_count': expiring_soon_count,
        'l1_count': l1_count,
        'l2_count': l2_count,
        'l3_count': l3_count,
    }
    return render(request, 'accounts/admin_dashboard.html', context)


@login_required
def approve_trainer(request, trainer_id):
    """Admin approves a pending trainer"""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('landing_page')
    
    trainer_profile = get_object_or_404(TrainerProfile, id=trainer_id, approval_status='PENDING')
    trainer_user = trainer_profile.user
    
    # Approve the trainer
    trainer_profile.approval_status = 'APPROVED'
    trainer_profile.approved_by = request.user
    trainer_profile.approval_date = timezone.now()
    trainer_profile.save()
    
    # Activate the user account
    trainer_user.is_active = True
    trainer_user.save()
    
    # Send approval email
    subject = 'HealthHub - Trainer Account Approved'
    message = f"""
Dear {trainer_user.full_name},

Congratulations! Your trainer account has been approved by the admin.

You can now login to your trainer dashboard using your credentials:
- Username: {trainer_user.username}
- Login URL: http://127.0.0.1:8000/login/

Approved By: {request.user.full_name}
Approval Date: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}

Welcome to the HealthHub team!

Best regards,
The HealthHub Team
Where Fitness Meets Wellness
"""
    
    try:
        email = EmailMessage(
            subject=subject,
            body=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[trainer_user.email]
        )
        email.send(fail_silently=False)
    except Exception as e:
        print(f"Error sending email: {e}")
    
    messages.success(request, f'Trainer {trainer_user.full_name} has been approved successfully!')
    return redirect('admin_dashboard')


@login_required
def reject_trainer(request, trainer_id):
    """Admin rejects a pending trainer"""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('landing_page')
    
    trainer_profile = get_object_or_404(TrainerProfile, id=trainer_id, approval_status='PENDING')
    trainer_user = trainer_profile.user
    
    if request.method == 'POST':
        rejection_reason = request.POST.get('rejection_reason', 'Not specified')
        
        # Reject the trainer
        trainer_profile.approval_status = 'REJECTED'
        trainer_profile.approved_by = request.user
        trainer_profile.approval_date = timezone.now()
        trainer_profile.rejection_reason = rejection_reason
        trainer_profile.save()
        
        # Keep user account inactive
        trainer_user.is_active = False
        trainer_user.save()
        
        # Send rejection email
        subject = 'HealthHub - Trainer Application Status'
        message = f"""
Dear {trainer_user.full_name},

We regret to inform you that your trainer application has not been approved at this time.

Reason: {rejection_reason}

If you believe this is an error or would like to reapply, please contact us at {settings.DEFAULT_FROM_EMAIL}.

Thank you for your interest in HealthHub.

Best regards,
The HealthHub Team
Where Fitness Meets Wellness
"""
        
        try:
            email = EmailMessage(
                subject=subject,
                body=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[trainer_user.email]
            )
            email.send(fail_silently=False)
        except Exception as e:
            print(f"Error sending email: {e}")
        
        messages.success(request, f'Trainer {trainer_user.full_name} application has been rejected.')
        return redirect('admin_dashboard')
    
    # If GET request, return to admin dashboard
    return redirect('admin_dashboard')


@login_required
def trainer_dashboard(request):
    """Trainer dashboard - view personal info and assigned clients"""
    if request.user.role != 'TRAINER':
        messages.error(request, 'Access denied. Trainer only.')
        return redirect('landing_page')
    
    trainer_profile = TrainerProfile.objects.get(user=request.user)
    assigned_clients = request.user.assigned_clients.all().select_related('membership__user')
    
    context = {
        'trainer_profile': trainer_profile,
        'assigned_clients': assigned_clients,
        'total_clients': assigned_clients.count(),
    }
    return render(request, 'accounts/trainer_dashboard.html', context)


@login_required
def user_dashboard(request):
    """User dashboard - view personal membership info"""
    if request.user.role != 'USER':
        messages.error(request, 'Access denied. User only.')
        return redirect('landing_page')
    
    try:
        from memberships.models import L3Addon, TrainerRating
        
        membership = UserMembership.objects.get(user=request.user)
        addons = membership.l3_addons.all()
        
        # Get L3 assigned trainers with ratings
        assigned_trainers = []
        if membership.membership_tier == 'L3':
            for addon in addons:
                if addon.assigned_trainer and addon.addon_type == 'TRAINER':
                    # Check if user has rated this trainer
                    existing_rating = TrainerRating.objects.filter(
                        user=request.user,
                        trainer=addon.assigned_trainer,
                        membership=membership
                    ).first()
                    
                    assigned_trainers.append({
                        'trainer': addon.assigned_trainer,
                        'existing_rating': existing_rating
                    })
        
        # Get current week workout plans for L2 users
        workout_plans = []
        if membership.membership_tier == 'L2':
            current_date = timezone.now().date()
            workout_plans = WorkoutPlan.objects.filter(
                membership=membership,
                start_date__lte=current_date,
                end_date__gte=current_date,
                is_active=True
            ).prefetch_related('exercises').order_by('day_of_week')
        
        # Get protein intake records if extra protein is needed
        protein_intakes = []
        if membership.extra_protein_needed:
            protein_intakes = ProteinIntake.objects.filter(
                membership=membership
            ).order_by('-date')[:30]  # Last 30 days
        
        # Get medical checkups if medical history exists
        medical_checkups = []
        if membership.medical_history:
            medical_checkups = MedicalCheckup.objects.filter(
                membership=membership
            ).order_by('-checkup_date')[:10]  # Last 10 checkups
            
    except UserMembership.DoesNotExist:
        membership = None
        addons = []
        assigned_trainers = []
        workout_plans = []
        protein_intakes = []
        medical_checkups = []
    
    # Check membership expiry
    expiry_warning = False
    expiry_date = None
    days_remaining = None
    if membership:
        expiry_date = membership.get_membership_expiry_date()
        expiry_warning = membership.is_expiring_soon()
        days_remaining = membership.days_until_expiry()
    
    context = {
        'membership': membership,
        'addons': addons,
        'assigned_trainers': assigned_trainers,
        'workout_plans': workout_plans,
        'protein_intakes': protein_intakes,
        'medical_checkups': medical_checkups,
        'expiry_warning': expiry_warning,
        'expiry_date': expiry_date,
        'days_remaining': days_remaining,
    }
    return render(request, 'accounts/user_dashboard.html', context)


@login_required
def admin_edit_user(request, user_id):
    """Admin can edit user details"""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('landing_page')
    
    from django.shortcuts import get_object_or_404
    user_to_edit = get_object_or_404(User, id=user_id)
    
    if request.method == 'POST':
        # Update basic user info
        user_to_edit.full_name = request.POST.get('full_name')
        user_to_edit.email = request.POST.get('email')
        user_to_edit.phone_number = request.POST.get('phone_number')
        user_to_edit.save()
        
        # Update role-specific info
        if user_to_edit.role == 'TRAINER':
            trainer_profile = user_to_edit.trainer_profile
            trainer_profile.specialization = request.POST.get('specialization')
            trainer_profile.experience_years = request.POST.get('experience_years')
            trainer_profile.qualification = request.POST.get('qualification')
            trainer_profile.certification_details = request.POST.get('certification_details')
            trainer_profile.save()
        elif user_to_edit.role == 'ADMIN':
            admin_profile = user_to_edit.admin_profile
            admin_profile.qualification = request.POST.get('qualification')
            admin_profile.save()
        
        messages.success(request, f'{user_to_edit.full_name} details updated successfully.')
        return redirect('admin_dashboard')
    
    return redirect('admin_dashboard')


@login_required
@require_POST
def toggle_exercise_completion(request):
    """Toggle exercise completion status"""
    if request.user.role != 'USER':
        return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)
    
    exercise_id = request.POST.get('exercise_id')
    try:
        exercise = Exercise.objects.get(id=exercise_id, workout_plan__membership__user=request.user)
        exercise.is_completed = not exercise.is_completed
        if exercise.is_completed:
            exercise.completed_at = timezone.now()
        else:
            exercise.completed_at = None
        exercise.save()
        
        return JsonResponse({
            'success': True,
            'is_completed': exercise.is_completed,
            'completed_at': exercise.completed_at.strftime('%Y-%m-%d %H:%M') if exercise.completed_at else None
        })
    except Exercise.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Exercise not found'}, status=404)


@login_required
def admin_manage_user_data(request, user_id):
    """Admin view to manage user's workout, protein intake, and medical checkups"""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('landing_page')
    
    user = get_object_or_404(User, id=user_id, role='USER')
    try:
        membership = UserMembership.objects.get(user=user)
    except UserMembership.DoesNotExist:
        messages.error(request, 'User has no membership.')
        return redirect('admin_dashboard')
    
    # Get current week workout plans
    current_date = timezone.now().date()
    workout_plans = WorkoutPlan.objects.filter(
        membership=membership,
        start_date__lte=current_date,
        end_date__gte=current_date,
        is_active=True
    ).prefetch_related('exercises').order_by('day_of_week')
    
    # Get protein intake records
    protein_intakes = ProteinIntake.objects.filter(
        membership=membership
    ).order_by('-date')[:30]
    
    # Get medical checkups
    medical_checkups = MedicalCheckup.objects.filter(
        membership=membership
    ).order_by('-checkup_date')
    
    context = {
        'managed_user': user,
        'membership': membership,
        'workout_plans': workout_plans,
        'protein_intakes': protein_intakes,
        'medical_checkups': medical_checkups,
    }
    return render(request, 'accounts/admin_manage_user.html', context)


@login_required
@require_POST
def admin_update_protein_intake(request):
    """Admin updates protein intake for a user"""
    if request.user.role != 'ADMIN':
        return JsonResponse({'success': False, 'error': 'Access denied'}, status=403)
    
    membership_id = request.POST.get('membership_id')
    date_str = request.POST.get('date')
    morning = request.POST.get('morning') == 'true'
    evening = request.POST.get('evening') == 'true'
    notes = request.POST.get('notes', '')
    
    try:
        membership = UserMembership.objects.get(id=membership_id)
        date_obj = datetime.strptime(date_str, '%Y-%m-%d').date()
        
        protein_intake, created = ProteinIntake.objects.update_or_create(
            membership=membership,
            date=date_obj,
            defaults={
                'morning_intake': morning,
                'evening_intake': evening,
                'notes': notes,
                'updated_by_admin': request.user
            }
        )
        
        return JsonResponse({
            'success': True,
            'message': 'Protein intake updated successfully'
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=400)


@login_required
def admin_create_workout_plan(request, user_id):
    """Admin creates/updates workout plan for L2 user"""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('landing_page')
    
    user = get_object_or_404(User, id=user_id, role='USER')
    membership = get_object_or_404(UserMembership, user=user, membership_tier='L2')
    
    if request.method == 'POST':
        week_number = int(request.POST.get('week_number', 1))
        start_date = datetime.strptime(request.POST.get('start_date'), '%Y-%m-%d').date()
        end_date = start_date + timedelta(days=6)
        
        # Create workout plans for 6 days
        days = ['MON', 'TUE', 'WED', 'THU', 'FRI', 'SAT']
        
        for day in days:
            workout_plan, created = WorkoutPlan.objects.get_or_create(
                membership=membership,
                week_number=week_number,
                day_of_week=day,
                defaults={
                    'start_date': start_date,
                    'end_date': end_date,
                    'is_active': True
                }
            )
            
            # Get exercises for this day from POST data
            exercise_count = int(request.POST.get(f'{day}_exercise_count', 0))
            for i in range(exercise_count):
                exercise_name = request.POST.get(f'{day}_exercise_{i}_name')
                exercise_type = request.POST.get(f'{day}_exercise_{i}_type')
                sets = request.POST.get(f'{day}_exercise_{i}_sets', 1)
                reps = request.POST.get(f'{day}_exercise_{i}_reps', 1)
                description = request.POST.get(f'{day}_exercise_{i}_description', '')
                
                if exercise_name:
                    Exercise.objects.create(
                        workout_plan=workout_plan,
                        exercise_name=exercise_name,
                        exercise_type=exercise_type,
                        sets=sets,
                        reps=reps,
                        description=description,
                        order=i
                    )
        
        messages.success(request, f'Workout plan for week {week_number} created successfully!')
        return redirect('admin_manage_user_data', user_id=user_id)
    
    # Generate AI-based workout suggestions
    context = {
        'managed_user': user,
        'membership': membership,
    }
    return render(request, 'accounts/admin_create_workout.html', context)


@login_required
def admin_add_medical_checkup(request, user_id):
    """Admin adds medical checkup record"""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Admin only.')
        return redirect('landing_page')
    
    user = get_object_or_404(User, id=user_id, role='USER')
    membership = get_object_or_404(UserMembership, user=user)
    
    if request.method == 'POST':
        checkup_date = datetime.strptime(request.POST.get('checkup_date'), '%Y-%m-%d').date()
        checkup_type = request.POST.get('checkup_type')
        status = request.POST.get('status', 'SCHEDULED')
        findings = request.POST.get('findings', '')
        recommendations = request.POST.get('recommendations', '')
        conducted_by = request.POST.get('conducted_by', '')
        next_checkup = request.POST.get('next_checkup_date')
        
        next_checkup_date = None
        if next_checkup:
            next_checkup_date = datetime.strptime(next_checkup, '%Y-%m-%d').date()
        
        MedicalCheckup.objects.create(
            membership=membership,
            checkup_date=checkup_date,
            checkup_type=checkup_type,
            status=status,
            findings=findings,
            recommendations=recommendations,
            next_checkup_date=next_checkup_date,
            conducted_by=conducted_by,
            updated_by_admin=request.user
        )
        
        messages.success(request, 'Medical checkup record added successfully!')
        return redirect('admin_manage_user_data', user_id=user_id)
    
    context = {
        'managed_user': user,
        'membership': membership,
    }
    return render(request, 'accounts/admin_add_checkup.html', context)

@login_required
def workout_progress_chart(request, user_id=None):
    """View workout progress charts for L2 users"""
    # Determine which user to show stats for
    if user_id and request.user.role == 'ADMIN':
        user = get_object_or_404(User, id=user_id, role='USER')
    else:
        user = request.user
        if user.role != 'USER':
            messages.error(request, 'Access denied.')
            return redirect('landing_page')
    
    try:
        membership = UserMembership.objects.get(user=user)
        if membership.membership_tier != 'L2':
            messages.error(request, 'Workout charts are only available for L2 members.')
            return redirect('user_dashboard' if request.user.role == 'USER' else 'admin_dashboard')
    except UserMembership.DoesNotExist:
        messages.error(request, 'No membership found.')
        return redirect('user_dashboard' if request.user.role == 'USER' else 'admin_dashboard')
    
    # Get all workout plans for this user
    workout_plans = WorkoutPlan.objects.filter(
        membership=membership
    ).prefetch_related('exercises').order_by('week_number', 'day_of_week')
    
    # Calculate statistics
    weekly_stats = {}
    day_stats = {
        'MON': {'total': 0, 'completed': 0},
        'TUE': {'total': 0, 'completed': 0},
        'WED': {'total': 0, 'completed': 0},
        'THU': {'total': 0, 'completed': 0},
        'FRI': {'total': 0, 'completed': 0},
        'SAT': {'total': 0, 'completed': 0},
    }
    
    for plan in workout_plans:
        week = plan.week_number
        if week not in weekly_stats:
            weekly_stats[week] = {
                'total_exercises': 0,
                'completed_exercises': 0,
                'start_date': plan.start_date,
                'end_date': plan.end_date
            }
        
        exercises = plan.exercises.all()
        total_count = exercises.count()
        completed_count = exercises.filter(is_completed=True).count()
        
        weekly_stats[week]['total_exercises'] += total_count
        weekly_stats[week]['completed_exercises'] += completed_count
        
        # Day-wise statistics
        day_stats[plan.day_of_week]['total'] += total_count
        day_stats[plan.day_of_week]['completed'] += completed_count
    
    # Calculate percentages
    for week in weekly_stats:
        if weekly_stats[week]['total_exercises'] > 0:
            weekly_stats[week]['completion_rate'] = round(
                (weekly_stats[week]['completed_exercises'] / weekly_stats[week]['total_exercises']) * 100, 1
            )
        else:
            weekly_stats[week]['completion_rate'] = 0
    
    for day in day_stats:
        if day_stats[day]['total'] > 0:
            day_stats[day]['completion_rate'] = round(
                (day_stats[day]['completed'] / day_stats[day]['total']) * 100, 1
            )
        else:
            day_stats[day]['completion_rate'] = 0
    
    # Overall statistics
    total_exercises = sum(ws['total_exercises'] for ws in weekly_stats.values())
    completed_exercises = sum(ws['completed_exercises'] for ws in weekly_stats.values())
    overall_completion_rate = round((completed_exercises / total_exercises * 100), 1) if total_exercises > 0 else 0
    
    context = {
        'target_user': user,
        'membership': membership,
        'weekly_stats': dict(sorted(weekly_stats.items())),
        'day_stats': day_stats,
        'total_exercises': total_exercises,
        'completed_exercises': completed_exercises,
        'overall_completion_rate': overall_completion_rate,
        'is_admin_viewing': request.user.role == 'ADMIN' and user != request.user,
    }
    return render(request, 'accounts/workout_progress_chart.html', context)


@login_required
def confirm_payment(request, user_id):
    """Admin confirms user payment"""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('login')
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('admin_dashboard')
    
    membership = get_object_or_404(UserMembership, user_id=user_id)
    
    if membership.payment_status == 'PAID':
        messages.warning(request, f'Payment for {membership.user.full_name} is already confirmed.')
        return redirect('admin_dashboard')
    
    # Update payment status
    membership.payment_status = 'PAID'
    membership.payment_confirmed_by = request.user
    membership.payment_confirmed_date = timezone.now()
    membership.payment_notes = request.POST.get('payment_notes', '')
    
    membership.save()
    
    messages.success(request, f'Payment confirmed for {membership.user.full_name}!')
    return redirect('admin_dashboard')


@login_required
def cancel_payment(request, user_id):
    """Admin cancels user payment"""
    if request.user.role != 'ADMIN':
        messages.error(request, 'Access denied. Admin privileges required.')
        return redirect('login')
    
    if request.method != 'POST':
        messages.error(request, 'Invalid request method.')
        return redirect('admin_dashboard')
    
    membership = get_object_or_404(UserMembership, user_id=user_id)
    
    if membership.payment_status == 'PAID':
        messages.warning(request, f'Cannot cancel already confirmed payment for {membership.user.full_name}.')
        return redirect('admin_dashboard')
    
    # Update payment status
    membership.payment_status = 'CANCELLED'
    membership.payment_confirmed_by = request.user
    membership.payment_confirmed_date = timezone.now()
    membership.payment_notes = request.POST.get('cancellation_reason', '')
    
    membership.save()
    
    messages.success(request, f'Payment cancelled for {membership.user.full_name}.')
    return redirect('admin_dashboard')


def approved_trainers_list(request):
    """View approved trainers with ratings - supports both HTML and JSON format"""
    from memberships.models import TrainerRating
    
    # Get all approved trainers
    approved_trainers = TrainerProfile.objects.filter(
        approval_status='APPROVED'
    ).select_related('user', 'approved_by')
    
    # Add rating information to each trainer
    trainers_with_ratings = []
    for trainer_profile in approved_trainers:
        ratings = TrainerRating.objects.filter(trainer=trainer_profile.user)
        avg_rating = ratings.aggregate(Avg('rating'))['rating__avg'] or 0
        rating_count = ratings.count()
        
        trainers_with_ratings.append({
            'profile': trainer_profile,
            'avg_rating': round(avg_rating, 1),
            'rating_count': rating_count,
            'ratings': ratings[:5]  # Get latest 5 ratings for preview
        })
    
    # Check if JSON format requested (for API)
    if request.GET.get('format') == 'json':
        trainers_json = []
        for item in trainers_with_ratings:
            trainer = item['profile']
            trainers_json.append({
                'id': trainer.user.id,
                'full_name': trainer.user.full_name,
                'email': trainer.user.email,
                'phone': trainer.user.phone_number,
                'specialization': trainer.specialization,
                'qualification': trainer.qualification,
                'experience_years': trainer.experience_years,
                'certification_details': trainer.certification_details,
                'licenses': trainer.licenses,
                'accreditations': trainer.accreditations,
                'approval_date': trainer.approval_date.strftime('%Y-%m-%d') if trainer.approval_date else None,
                'avg_rating': item['avg_rating'],
                'rating_count': item['rating_count']
            })
        
        return JsonResponse({
            'total_trainers': len(trainers_json),
            'trainers': trainers_json
        })
    
    # HTML response
    context = {
        'trainers_with_ratings': trainers_with_ratings,
        'total_approved': len(trainers_with_ratings)
    }
    return render(request, 'accounts/approved_trainers.html', context)
    return redirect('admin_dashboard')