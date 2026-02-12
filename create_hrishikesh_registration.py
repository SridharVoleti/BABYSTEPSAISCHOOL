"""
Script to create student registration for Hrishikesh - Class 5
Author: Cascade AI
Date: 2025-12-13
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from student_registration.models import StudentRegistration
from datetime import date

registration = StudentRegistration.objects.create(
    student_name='Hrishikesh',
    student_email='hrishikesh@babysteps.edu',
    parent_name='Hrishikesh Parent',
    parent_email='hrishikesh.parent@babysteps.edu',
    phone='9876543210',
    grade='5',
    school_name='BabySteps Digital School',
    address='123 Main Street',
    city='Hyderabad',
    state='Telangana',
    pincode='500001',
    date_of_birth=date(2014, 1, 15),
    preferred_language='english'
)

print(f'✅ Successfully created registration!')
print(f'   Student: {registration.student_name}')
print(f'   Grade: {registration.grade}')
print(f'   Email: {registration.student_email}')
print(f'   Status: {registration.status}')
print(f'   Registration ID: {registration.registration_id}')
print(f'\n📋 You can now approve this registration using:')
print(f'   - Django Admin: http://127.0.0.1:8000/admin/student_registration/studentregistration/')
print(f'   - API Endpoint: POST http://127.0.0.1:8000/api/registrations/{registration.registration_id}/approve/')
