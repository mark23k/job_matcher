from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from .models import Candidate, Tag, CustomUser
from .forms import CandidateForm, TagForm, CandidateSelectionForm, CustomUserCreationForm
from django.db.models import Q
from django.core.mail import send_mail
from django.conf import settings
from .utils import summarize_cv, send_bulk_email
import logging
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.views import LoginView
from django.urls import reverse
from django.db.models import QuerySet 
from django.contrib import messages

def is_admin(user):
    return user.is_superuser

# Set up logging
logger = logging.getLogger(__name__)



# Custom login view to redirect based on user type

class CustomLoginView(LoginView):
    template_name = 'matcher/login.html'  # Use your custom template path here

    def get_redirect_url(self):
    # Check for 'superuser' and groups
        if self.request.user.is_superuser:
            return reverse('admin_dashboard')  # Admin redirect
        return reverse('regular_dashboard')  # Default to regular_dashboard if the group is undefined



@login_required
def home(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')  # Admins are redirected to the admin dashboard
    else:
        return redirect('regular_dashboard')  # Regular users are redirected to the user home page


@login_required
def admin_dashboard(request):
    return render(request, 'matcher/admin_dashboard.html', {'user': request.user})


# View for regular users
@login_required
def regular_dashboard(request):
    if request.user.groups.filter(name='regular_user').exists():  # Adjust if you use another group
        return render(request, 'matcher/regular_dashboard.html', {'user': request.user})
    else:
        return redirect('admin_dashboard')
    

 


@login_required
@user_passes_test(is_admin)
def add_candidate(request):
    """Add a new candidate."""
    tags = Tag.objects.all()  # Get all available tags
    selected_tags = []  # Initialize selected_tags as an empty list

    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES)
        if form.is_valid():
            # Save candidate first
            candidate = form.save()

            # Handle the many-to-many relationship (tags)
            selected_tags = form.cleaned_data['tags']  # Get the tags from the form
            
            if isinstance(selected_tags, (list, QuerySet)):  # Ensure tags are in the correct format
                candidate.tags.set(selected_tags)  # Set tags to candidate using set() method
            else:
                logger.error("Selected tags are not in the expected format.")

            candidate.save()  # Save candidate after associating the tags
            return redirect('candidate_list')  # Redirect to the candidate list page
    else:
        form = CandidateForm()

    return render(request, 'matcher/add_candidate.html', {'form': form, 'tags': tags, 'selected_tags': selected_tags})



@login_required
def candidate_list(request):
    """List all candidates with search functionality."""
    search_query = request.GET.get('search', '')

    if search_query:
        candidates = Candidate.objects.filter(
            Q(name__icontains=search_query) |
            Q(tags__name__icontains=search_query) |
            Q(summary__icontains=search_query)
        ).distinct()
    else:
        candidates = Candidate.objects.all()

    return render(request, 'matcher/candidate_list.html', {'candidates': candidates, 'search_query': search_query})

@login_required
def candidate_detail(request, candidate_id):
    """View details of a single candidate."""
    candidate = get_object_or_404(Candidate, id=candidate_id)
    return render(request, 'matcher/candidate_detail.html', {'candidate': candidate})

@login_required
@user_passes_test(is_admin)
def add_tag(request):
    """Add a new tag."""
    message = ''
    if request.method == 'POST':
        form = TagForm(request.POST)
        if form.is_valid():
            form.save()
            message = 'Tag added successfully'
            form = TagForm()  # Reset form for the next entry
    else:
        form = TagForm()

    return render(request, 'matcher/add_tags.html', {'form': form, 'message': message})

@login_required
def tag_list(request):
    """List all tags."""
    tags = Tag.objects.all()
    return render(request, 'matcher/tag_list.html', {'tags': tags})

@login_required
@user_passes_test(is_admin)
def confirm_delete_tag(request, tag_id):
    """Confirm the deletion of a tag."""
    tag = get_object_or_404(Tag, id=tag_id)

    if request.method == 'POST':
        tag.delete()
        logger.info(f"Tag deleted: {tag.name}")
        return redirect('tag_list')

    return render(request, 'matcher/confirm_delete_tag.html', {'tag': tag})

@login_required
@user_passes_test(is_admin)
def confirm_delete_candidate(request, candidate_id):
    """Confirm the deletion of a candidate."""
    candidate = get_object_or_404(Candidate, id=candidate_id)

    if request.method == 'POST':
        candidate.delete()
        logger.info(f"Candidate deleted: {candidate.name}")
        return redirect('candidate_list')

    return render(request, 'matcher/confirm_delete_candidate.html', {'candidate': candidate})

@login_required
@user_passes_test(is_admin)
def select_candidates(request):
    """Select candidates to include in a bulk email."""
    candidates = Candidate.objects.all()  # Fetch all candidates
    summaries = []

    if request.method == 'POST':
        form = CandidateSelectionForm(request.POST)
        if form.is_valid():
            selected_candidates = form.cleaned_data['candidates']  # Get selected candidates
            for candidate in selected_candidates:
                # Extract and summarize the CV for each selected candidate
                if candidate.cv:
                    summary = summarize_cv(candidate.cv)  # Replace with your actual summarization logic
                else:
                    summary = 'No CV uploaded'

                # Append candidate details along with email to the summaries list
                summaries.append({
                    'candidate_id': candidate.id,
                    'candidate_name': candidate.name,
                    'candidate_email': candidate.email,  # Ensure the email is included
                    'summary': summary
                })

            # Ensure summaries is a list and save to session
            if isinstance(summaries, list):
                request.session['summaries'] = summaries
            else:
                request.session['summaries'] = []

            # Redirect to the preview email page
            return redirect('preview_mail_shot')

    else:
        form = CandidateSelectionForm()

    return render(request, 'matcher/select_candidates.html', {'form': form, 'candidates': candidates})



def edit_candidate(request, candidate_id):
    """Edit an existing candidate."""
    candidate = get_object_or_404(Candidate, id=candidate_id)
    tags = Tag.objects.all()  # Get all available tags

    if request.method == 'POST':
        form = CandidateForm(request.POST, request.FILES, instance=candidate)
        if form.is_valid():
            # Save candidate first
            candidate = form.save()

            # Handle the many-to-many relationship (tags)
            selected_tags = form.cleaned_data['tags']  # Get the tags from the form

            if isinstance(selected_tags, (list, QuerySet)):  # Ensure tags are in the correct format
                candidate.tags.set(selected_tags)  # Set tags to candidate using set() method
            else:
                logger.error("Selected tags are not in the expected format.")

            candidate.save()  # Save candidate after associating the tags
            return redirect('candidate_list')  # Redirect to the candidate list page
    else:
        form = CandidateForm(instance=candidate)

    return render(request, 'matcher/edit_candidate.html', {'form': form, 'candidate': candidate, 'tags': tags})


@login_required
@user_passes_test(is_admin)
def preview_mail_shot(request):
    """
    Renders a preview of summarized CVs and provides options to send emails or go back to candidate selection.
    """
    summaries = request.session.get('summaries', [])

    # Ensure summaries is a list; reset if not
    if not isinstance(summaries, list):
        summaries = []  # Reset to an empty list if it's not valid

    if request.method == 'POST':
        # Check if the "send email" button was clicked
        if 'send_email' in request.POST:
            # Call the function to send bulk email
            send_bulk_email(summaries)

            # Clear summaries from the session after sending the email
            del request.session['summaries']

            # Redirect to the email sent confirmation page
            return redirect('email_sent')

        # Check if the "back to select candidates" button was clicked
        elif 'back_to_select' in request.POST:
            return redirect('select_candidates')

    # Render the preview page with summaries
    return render(request, 'matcher/preview_mail_shot.html', {'summaries': summaries})

       





@login_required
def email_sent(request):
    """Show confirmation after email is sent."""
    return render(request, 'matcher/email_sent.html')


def send_bulk_email(summaries):
    """Send a bulk email to selected candidates."""
    subject = "CV Summary Mail Shot"
    message = ""

    # Prepare the email content with all summaries
    for summary in summaries:
        message += f"<strong>{summary['candidate_name']}</strong>: {summary['summary']}<br><br>"

    # Prepare the recipient list, making sure to use the candidate's email
    recipient_list = [summary['candidate_email'] for summary in summaries if summary.get('candidate_email')]

    if not recipient_list:
        logger.warning("No valid recipient emails found.")
        return

    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipient_list,
        html_message=message  # Send HTML content
    )
    logger.info(f"Bulk email sent to {len(recipient_list)} recipients.")





@login_required
@user_passes_test(is_admin)
def register_new_user(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()

            # Get the selected group from the form and assign it to the user
            selected_group = form.cleaned_data.get('group')
            if selected_group:
                user.groups.add(selected_group)

            # Log the user in and redirect
            return redirect('admin_dashboard')  # Adjust based on your redirect destination
    else:
        form = CustomUserCreationForm()
    
    return render(request, 'register.html', {'form': form})

def users_list(request):
    """List all users with search functionality."""
    search_query = request.GET.get('search', '')

    if search_query:
        users = CustomUser.objects.filter(
            Q(username__icontains=search_query) |  # Searching by username, first name, or last name
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        ).distinct()
    else:
        users = CustomUser.objects.all()

    return render(request, 'matcher/users_list.html', {'users': users, 'search_query': search_query})

def user_detail(request, user_id):
    """View details of a single user."""
    user = get_object_or_404(CustomUser, pk=user_id)
    return render(request, 'matcher/user_detail.html', {'user': user})


def confirm_delete_user(request, user_id):
    """Confirm the deletion of a tag."""
    user = get_object_or_404(CustomUser, pk=user_id)

    if request.method == 'POST':
        user.delete()
        logger.info(f"User deleted: {user.username}")
        return redirect('users_list')

    return render(request, 'matcher/confirm_delete_user.html', {'user': user})



def user_profile(request):
    return render(request, 'matcher/user_profile.html')
