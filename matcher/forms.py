from django import forms
from .models import Candidate, Tag
from django.core.exceptions import ValidationError
import os
from django.db.models import Q
from django.contrib.auth.models import Group
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):
    group = forms.ModelChoiceField(queryset=Group.objects.all(), required=False, empty_label="Select Group")

    class Meta:
        model = CustomUser
        fields = ('username', 'first_name', 'last_name', 'email', 'group')  # Add group to the form fields



class CandidateForm(forms.ModelForm):
    """Form for adding and editing candidates."""
    tags = forms.ModelMultipleChoiceField(queryset=Tag.objects.all(), required=False)  # Ensure this is ModelMultipleChoiceField

    class Meta:
        model = Candidate
        fields = ['name', 'email', 'phone_number', 'tags', 'cv']

    def clean_cv(self):
        """Validate the CV file format to ensure it's either PDF or DOCX."""
        cv = self.cleaned_data.get('cv', None)

        if cv:
            # Get the file extension
            file_extension = os.path.splitext(cv.name)[1].lower()

            # Check if the file is either a PDF or .docx
            if file_extension not in ['.pdf', '.docx']:
                raise ValidationError("Only PDF and .docx files are allowed.")

        return cv

    def save(self, commit=True):
        """Override save method to ensure `tags` are handled correctly."""
        instance = super().save(commit=False)

        # Don't save immediately, we'll handle saving tags separately
        if commit:
            instance.save()

        # Save many-to-many field (tags)
        self.save_m2m()

        return instance



class TagForm(forms.ModelForm):
    """Form for adding and editing tags."""
    class Meta:
        model = Tag
        fields = ['name']

    def clean_name(self):
        """Ensure that the tag name is unique and handle case-insensitivity."""
        name = self.cleaned_data.get('name').lower()  # Convert to lowercase
        if Tag.objects.filter(name=name).exists():
            raise ValidationError(f"The tag '{name}' already exists.")
        return name


class CandidateSelectionForm(forms.Form):
    """Form to select multiple candidates for email summary or other actions."""
    candidates = forms.ModelMultipleChoiceField(
        queryset=Candidate.objects.filter(active=True),  # Only active candidates
        widget=forms.CheckboxSelectMultiple,
        required=True,
    )


class SearchForm(forms.Form):
    """Form for searching candidates by name, tags, or keywords."""
    search_query = forms.CharField(required=False, label='Search', max_length=100)

    def search_candidates(self):
        """Search candidates by name, tags, or summary."""
        search_query = self.cleaned_data.get('search_query')
        if search_query:
            return Candidate.objects.filter(
                Q(name__icontains=search_query) |
                Q(tags__name__icontains=search_query) |
                Q(summary__icontains=search_query)
            ).distinct()
        return Candidate.objects.all()
