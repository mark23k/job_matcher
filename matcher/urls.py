from django.urls import path
from . import views

urlpatterns = [
    # Authentication Views
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('register/', views.register_new_user, name='register'),
 

    # Home Views
    path('', views.home, name='home'),  # Redirect to user or admin home based on role
    path('regular_dashboard/', views.regular_dashboard, name='regular_dashboard'),  # Regular user's dashboard
    path('admin_dashboard/', views.admin_dashboard, name='admin_dashboard'),  # Admin's dashboard
    path('users_list/', views.users_list, name='users_list'),
    path('user/<int:user_id>/', views.user_detail, name='user_detail'),
    path('confirm_delete_user/<int:user_id>/', views.confirm_delete_user, name='confirm_delete_user'),  # Confirm delete candidate


    # Candidate Views
    path('edit_candidate/<int:candidate_id>/', views.edit_candidate, name='edit_candidate'), 
    path('candidates/', views.candidate_list, name='candidate_list'),  # List all candidates
    path('candidate/<int:candidate_id>/', views.candidate_detail, name='candidate_detail'),  # Candidate detail page
    path('add_candidate/', views.add_candidate, name='add_candidate'),  # Add a new candidate
    path('confirm_delete_candidate/<int:candidate_id>/', views.confirm_delete_candidate, name='confirm_delete_candidate'),  # Confirm delete candidate

    # Tag Views
    path('tags/', views.tag_list, name='tag_list'),  # List all tags
    path('add_tag/', views.add_tag, name='add_tag'),  # Add a new tag
    path('confirm_delete_tag/<int:tag_id>/', views.confirm_delete_tag, name='confirm_delete_tag'),  # Confirm delete tag

    # Bulk Email Views
    path('select_candidates/', views.select_candidates, name='select_candidates'),  # Select candidates for email
    path('preview_mail_shot/', views.preview_mail_shot, name='preview_mail_shot'),  # Preview email before sending
    path('email_sent/', views.email_sent, name='email_sent'),  # Confirmation after email is sent

    # User Profile
    path('profile/', views.user_profile, name='user_profile'),  # User profile page

]
