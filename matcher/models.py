from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
import re
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    """Custom user model to add additional fields."""
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return self.username

class Tag(models.Model):
    """Model for tags associated with candidates."""
    name = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.name

class Candidate(models.Model):
    """Model for storing candidate information."""
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=20)
    tags = models.ManyToManyField(Tag, related_name='candidates', blank=True)
    cv = models.FileField(upload_to='cvs/', blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    active = models.BooleanField(default=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        """
        Override the save method to handle additional logic.
        """
        super().save(*args, **kwargs)  # Call the parent save method
