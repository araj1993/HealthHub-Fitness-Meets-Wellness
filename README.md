# HealthHub - Where Fitness Meets Wellness

A comprehensive Django-based fitness management system with role-based registration (Admin, User, Trainer) and tiered membership plans.

## Features

### 🎯 Three User Roles

#### 1. Admin Registration
- Full system management access
- Common fields + Admin-specific fields:
  - Qualification
  - Security PIN (optional)

#### 2. User Registration (Members)
- Three membership tiers with progressive features
- PDF receipt generation after registration
- Flexible payment options with discounts

**Membership Tiers:**

**L1 - FitStarter (₹1,500/month)**
- Basic gym access
- Standard equipment
- Health tracking

**L2 - ProActive (₹2,500/month)**
- All L1 features +
- AI Workout Planner
- Nutrition Recommendations
- Weekly Performance Insights
- Stress & Activity Analysis
- Optional protein supplementation

**L3 - EliteChamp (₹2,500/month + add-ons)**
- All L1 + L2 features +
- Daily protein shake (40g)
- Premium add-ons (₹1,000 each):
  - Personal Trainer Booking
  - Zumba & Martial Arts (Live/Recorded)
  - Premium Nutrition Hub
  - Mental Wellness Dashboard

#### 3. Trainer Registration
- Professional fitness coaching access
- Common fields + Trainer-specific fields:
  - Qualification
  - Specialization (Fitness, Yoga, Strength, etc.)
  - Years of Experience
  - Certification Details

### 💰 Fee Calculation System

**Base Structure:**
- Registration Fee: ₹2,000 (all tiers)
- Monthly fees based on tier selection
- Advance payment option with discounts:
  - Pay for more than 2 months: ₹200 discount per extra month
  - Example: 5 months = ₹200 × 3 = ₹600 discount

**L3 Add-ons:**
- Each checkbox feature adds ₹1,000

### 📄 PDF Receipt Generation

Automatically generated for user registrations with:
- Member information
- Membership tier and amenities
- Complete fee breakdown
- Unique registration ID
- Receipt number and date
- Downloadable PDF format

## Installation

### Prerequisites
- Python 3.8+
- pip
- Virtual environment (recommended)

### Setup Instructions

1. **Clone or navigate to the project directory:**
```bash
cd "c:\Users\KIRAN\Documents\araj1993-git\FINAL\HealthHub-Where-Fitness-Meets-Wellness"
```

2. **Activate virtual environment:**
```powershell
& "C:/Users/KIRAN/Documents/araj1993-git/FINAL/.venv/Scripts/Activate.ps1"
```

3. **Install dependencies:**
```bash
pip install django djangorestframework pillow django-cors-headers reportlab
```

4. **Run migrations:**
```bash
python manage.py migrate
```

5. **Create superuser (for admin panel access):**
```bash
python manage.py createsuperuser
```

6. **Create media directories:**
```bash
mkdir media
mkdir media\receipts
mkdir media\profile_photos
```

7. **Run the development server:**
```bash
python manage.py runserver
```

8. **Access the application:**
- Main application: http://127.0.0.1:8000/
- Admin panel: http://127.0.0.1:8000/admin/

## Project Structure

```
HealthHub-Where-Fitness-Meets-Wellness/
├── healthhub/              # Project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/               # User authentication & roles
│   ├── models.py          # User, AdminProfile, TrainerProfile
│   ├── forms.py           # Registration forms
│   ├── views.py           # Registration views
│   ├── admin.py           # Admin interface
│   └── urls.py
├── memberships/           # Membership management
│   ├── models.py         # UserMembership, L3Addon, PaymentReceipt
│   ├── forms.py          # Membership & add-on forms
│   ├── views.py          # Registration & success views
│   ├── utils.py          # PDF generation utility
│   ├── admin.py          # Admin interface
│   └── urls.py
├── templates/            # HTML templates
│   ├── base.html
│   ├── accounts/
│   │   ├── home.html
│   │   ├── register_admin.html
│   │   └── register_trainer.html
│   └── memberships/
│       ├── register_user.html
│       └── success.html
├── static/              # Static files (CSS, JS, images)
├── media/               # User uploads & generated files
│   ├── receipts/       # PDF receipts
│   └── profile_photos/ # User profile photos
└── manage.py

```

## Usage Guide

### Registering as Admin

1. Go to homepage
2. Click "Register as Admin"
3. Fill common information (name, email, phone, username, password, photo)
4. Fill admin-specific fields (qualification, security PIN)
5. Submit to complete registration

### Registering as Trainer

1. Go to homepage
2. Click "Register as Trainer"
3. Fill common information
4. Fill trainer-specific fields (qualification, specialization, experience, certifications)
5. Submit to complete registration

### Registering as User (Member)

1. Go to homepage
2. Click "Register as User"
3. Fill common information
4. **Select membership tier** (L1, L2, or L3)
5. Fill health information (age, weight, joining date, medical history)
6. Choose payment option:
   - Pay monthly in advance (with discount for 3+ months)
   - Select number of months
7. **For L2:** Indicate if extra protein is needed
8. **For L3:** Select add-on features (₹1,000 each):
   - Personal Trainer Booking
   - Zumba & Martial Arts
   - Premium Nutrition Hub
   - Mental Wellness Dashboard
9. Review fee summary in sidebar
10. Submit registration
11. **Download PDF receipt** from success page

## Key Features

✅ Role-based registration with common + role-specific fields
✅ Three-tier membership system (L1/L2/L3)
✅ Dynamic fee calculation with real-time updates
✅ Discount system for advance monthly payments
✅ L3 premium add-ons with checkbox selection
✅ Automatic PDF receipt generation
✅ Beautiful, responsive UI with Bootstrap 5
✅ Admin panel for managing all registrations
✅ File upload support for profile photos
✅ Secure password handling
✅ Comprehensive data validation

## Technologies Used

- **Backend:** Django 6.0
- **Database:** SQLite (development)
- **Frontend:** Bootstrap 5, jQuery
- **PDF Generation:** ReportLab
- **Image Handling:** Pillow
- **Icons:** Font Awesome 6

## Admin Panel Features

Access the admin panel at `/admin/` to:
- View all registered users (Admin, Trainer, User)
- Manage memberships and subscriptions
- View and download payment receipts
- Track L3 add-ons
- Monitor registration statistics
- Manage user profiles and permissions

## Development

### Running Tests
```bash
python manage.py test
```

### Creating Additional Superusers
```bash
python manage.py createsuperuser
```

### Collecting Static Files (for production)
```bash
python manage.py collectstatic
```

## Security Notes

- Change `SECRET_KEY` in production
- Set `DEBUG = False` in production
- Configure `ALLOWED_HOSTS` for production
- Use environment variables for sensitive data
- Implement HTTPS in production
- Set up proper database backups

## Future Enhancements

- Email notifications for registrations
- Payment gateway integration
- QR code on receipts
- Member dashboard
- Trainer booking system
- Workout tracking
- Nutrition planning tools
- Mobile app integration

## Support

For issues or questions, please contact:
- Email: support@healthhub.com
- Phone: +1-800-FITNESS

## License

This project is developed for HealthHub - Where Fitness Meets Wellness.

---

**Built with ❤️ using Django**
