# Generated by Django 3.0.7 on 2020-07-01 06:13

import datetime
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Room',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('room_number', models.IntegerField()),
                ('room_name', models.CharField(max_length=255)),
                ('school', models.CharField(choices=[('SEAS', 'School of Engineering and Applied Sciences'), ('SAS', 'School of Arts and Sciences'), ('AMSOM', 'Amrut Mody School of Management'), ('BLS', 'Biological Life Sciences'), ('SCS', 'School of Computer Studies'), ('NULL', 'UNASSIGNED')], default='NULL', max_length=10)),
                ('description', models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Booking',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('booking_date', models.DateField(default=datetime.date.today)),
                ('start_timing', models.TimeField()),
                ('end_timing', models.TimeField()),
                ('purpose_of_booking', models.TextField()),
                ('is_pending', models.BooleanField(default=False)),
                ('admin_did_accept', models.BooleanField(default=False)),
                ('admin_feedback', models.TextField(blank=True, default=None, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('Room', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to='BookingSystem.Room')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='bookings', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
