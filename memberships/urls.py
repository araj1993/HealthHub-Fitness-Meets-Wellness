from django.urls import path
from . import views

urlpatterns = [
    path('register/user/', views.register_user, name='register_user'),
    path('success/<int:membership_id>/', views.membership_success, name='membership_success'),
    path('fee-calculator/', views.fee_calculator_ajax, name='fee_calculator'),
    
    # Trainer rating URLs
    path('rate-trainer/<int:trainer_id>/', views.rate_trainer, name='rate_trainer'),
    path('trainer-ratings/<int:trainer_id>/', views.trainer_ratings, name='trainer_ratings'),
]
