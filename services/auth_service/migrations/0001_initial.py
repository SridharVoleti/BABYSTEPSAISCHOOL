# 2026-02-12: Initial migration for auth_service models

import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """2026-02-12: Create auth_service tables."""

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Parent',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('phone', models.CharField(db_index=True, max_length=15, unique=True)),
                ('full_name', models.CharField(max_length=150)),
                ('email', models.EmailField(blank=True, default='', max_length=254)),
                ('state', models.CharField(blank=True, default='', max_length=50)),
                ('preferred_language', models.CharField(default='en', max_length=20)),
                ('is_phone_verified', models.BooleanField(default=False)),
                ('is_profile_complete', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='parent_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='Student',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('full_name', models.CharField(max_length=150)),
                ('dob', models.DateField()),
                ('age_group', models.CharField(choices=[('3-6', 'Early Childhood (3-6)'), ('6-12', 'Middle Childhood (6-12)'), ('12+', 'Adolescent (12+)')], max_length=5)),
                ('grade', models.IntegerField()),
                ('login_method', models.CharField(choices=[('picture', 'Picture Sequence'), ('pin', 'PIN Code'), ('password', 'Password')], max_length=10)),
                ('avatar_id', models.CharField(default='avatar_01', max_length=50)),
                ('picture_sequence_hash', models.CharField(blank=True, default='', max_length=128)),
                ('pin_hash', models.CharField(blank=True, default='', max_length=128)),
                ('language_1', models.CharField(default='English', max_length=30)),
                ('language_2', models.CharField(blank=True, default='', max_length=30)),
                ('language_3', models.CharField(blank=True, default='', max_length=30)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='students', to='auth_service.parent')),
                ('user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='student_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='OTPRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('phone', models.CharField(db_index=True, max_length=15)),
                ('otp_hash', models.CharField(max_length=128)),
                ('purpose', models.CharField(choices=[('registration', 'Registration'), ('login', 'Login'), ('reset', 'Password Reset')], default='registration', max_length=20)),
                ('attempts', models.IntegerField(default=0)),
                ('is_verified', models.BooleanField(default=False)),
                ('expires_at', models.DateTimeField()),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='ConsentRecord',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('consent_version', models.CharField(max_length=20)),
                ('action', models.CharField(choices=[('grant', 'Grant'), ('withdraw', 'Withdraw')], max_length=10)),
                ('scroll_percentage', models.IntegerField(default=0)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('parent', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='consent_records', to='auth_service.parent')),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('action', models.CharField(max_length=50)),
                ('resource_type', models.CharField(blank=True, default='', max_length=50)),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True)),
                ('metadata', models.JSONField(blank=True, default=dict)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-timestamp'],
            },
        ),
    ]
