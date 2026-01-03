from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing_page, name='landing_page'),
    path('register/', views.home, name='home'),
    path('register/admin/', views.register_admin, name='register_admin'),
    path('register/trainer/', views.register_trainer, name='register_trainer'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('dashboard/admin/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/trainer/', views.trainer_dashboard, name='trainer_dashboard'),
    path('dashboard/user/', views.user_dashboard, name='user_dashboard'),
    path('dashboard/admin/edit-user/<int:user_id>/', views.admin_edit_user, name='admin_edit_user'),
    
    # Trainer approval URLs
    path('dashboard/admin/approve-trainer/<int:trainer_id>/', views.approve_trainer, name='approve_trainer'),
    path('dashboard/admin/reject-trainer/<int:trainer_id>/', views.reject_trainer, name='reject_trainer'),
    
    # Approved trainers list (public)
    path('trainers/', views.approved_trainers_list, name='approved_trainers_list'),
    
    # New URLs for workout, protein, and medical management
    path('toggle-exercise/', views.toggle_exercise_completion, name='toggle_exercise_completion'),
    path('dashboard/admin/manage-user/<int:user_id>/', views.admin_manage_user_data, name='admin_manage_user_data'),
    path('dashboard/admin/update-protein/', views.admin_update_protein_intake, name='admin_update_protein_intake'),
    path('dashboard/admin/create-workout/<int:user_id>/', views.admin_create_workout_plan, name='admin_create_workout_plan'),
    path('dashboard/admin/add-checkup/<int:user_id>/', views.admin_add_medical_checkup, name='admin_add_medical_checkup'),
    
    # Workout progress charts
    path('workout-progress/', views.workout_progress_chart, name='workout_progress_chart'),
    path('dashboard/admin/workout-progress/<int:user_id>/', views.workout_progress_chart, name='admin_workout_progress_chart'),
    
    # Payment confirmation URLs
    path('dashboard/admin/confirm-payment/<int:user_id>/', views.confirm_payment, name='confirm_payment'),
    path('dashboard/admin/cancel-payment/<int:user_id>/', views.cancel_payment, name='cancel_payment'),
]
