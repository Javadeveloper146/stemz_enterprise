
from datetime import timedelta
from django.db import models
from django import forms
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth.hashers import make_password, check_password
class UserProfile(models.Model):
    ROLE_CHOICES = [
        ('DEV', 'Developer'),
        ('TEST', 'Tester'),
        ('BA', 'Business Analyst'),
        ('MAN', 'Manager'),
    ]

    DEPARTMENT_CHOICES = [
        ('IT', 'IT'),
    ]

    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=128)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    department = models.CharField(max_length=10, choices=DEPARTMENT_CHOICES)
    active_status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def set_password(self, raw_password):
            self.password = make_password(raw_password)

    def check_password(self, raw_password):
            return check_password(raw_password, self.password)

    def __str__(self):
        return self.username


class LoginRecord(models.Model):
    user = models.ForeignKey('UserProfile', on_delete=models.CASCADE)  # Reference to the UserProfile
    login_time = models.DateTimeField(default=timezone.now)  # Store login timestamp
    ip_address = models.GenericIPAddressField(null=True, blank=True)  # Store the user's IP address
    user_agent = models.TextField(null=True, blank=True)  # Optional: Store browser/OS info

    def __str__(self):
        return f'{self.user.username} logged in at {self.login_time}'
    

class TaskEntries(models.Model):
    EVENT_CHOICES = [
        ('Meeting', 'Meeting'),
        ('Development', 'Development'),
        ('Testing', 'Testing'),
        ('Review', 'Review'),
    ]

    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('In Progress', 'In Progress'),
        ('Completed', 'Completed'),
    ]

    user = models.ForeignKey('UserProfile', on_delete=models.CASCADE)
    event_type = models.CharField(max_length=50, choices=EVENT_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    task = models.TextField()
    status = models.CharField(max_length=50, choices=STATUS_CHOICES)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)
    total_duration = models.DurationField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username}'s task: {self.task}"

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError('Start time must be less than end time.')
    
    # Override the save method to calculate total_duration
    def save(self, *args, **kwargs):
        # Validate the start and end time before saving
        self.clean()

        if self.start_time and self.end_time:
            start = timedelta(hours=self.start_time.hour, minutes=self.start_time.minute)
            end = timedelta(hours=self.end_time.hour, minutes=self.end_time.minute)
            self.total_duration = end - start
        super(TaskEntries, self).save(*args, **kwargs)
        
        
class Chat(models.Model):
    user = models.ForeignKey('UserProfile', on_delete=models.CASCADE)
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    
    
    def __str__(self):
        return f'{self.user}: {self.text[:20]}'