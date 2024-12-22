from django.contrib import admin
from .models import Candidate, Tag, CustomUser
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.db.models import Count

# Register the CustomUser model with custom UserAdmin
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['username', 'email', 'is_verified', 'is_staff', 'is_superuser', 'last_login']
    list_filter = ['is_verified', 'is_staff', 'is_superuser', 'is_active']
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {'fields': ('is_verified', 'is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_verified', 'is_active', 'is_staff', 'is_superuser')}
        ),
    )
    search_fields = ['username', 'email']
    ordering = ['username']

# Register the CustomUserAdmin
admin.site.register(CustomUser, CustomUserAdmin)

# Register the Tag model
class TagAdmin(admin.ModelAdmin):
    list_display = ['name', 'candidate_count']  # Show number of candidates associated with the tag
    search_fields = ['name']
    ordering = ['name']

    def candidate_count(self, obj):
        """Display the number of candidates associated with the tag."""
        return obj.candidate_set.count()  # Counts candidates associated with this tag

    candidate_count.short_description = 'Number of Candidates'

admin.site.register(Tag, TagAdmin)

# Register the Candidate model
class CandidateAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'phone_number', 'active', 'uploaded_at', 'summary_preview']
    list_filter = ['active', 'uploaded_at', 'tags']
    search_fields = ['name', 'email', 'phone_number', 'summary']
    ordering = ['uploaded_at']
    filter_horizontal = ('tags',)  # For a better UI with the many-to-many relationship with tags

    # Optional summary preview for easier identification of candidate
    def summary_preview(self, obj):
        """Display a truncated preview of the summary."""
        return obj.summary[:50]  # Show the first 50 characters of the summary

    summary_preview.short_description = 'Summary Preview'

    def get_queryset(self, request):
        """Filter candidates based on custom conditions like user permissions."""
        queryset = super().get_queryset(request)
        if not request.user.is_superuser:
            queryset = queryset.filter(active=True)  # Show only active candidates for non-admin users
        return queryset

    def save_model(self, request, obj, form, change):
        """Update the search vector when saving a candidate."""
        obj.search_vector = obj.search_vector_property  # Update the search vector
        super().save_model(request, obj, form, change)

admin.site.register(Candidate, CandidateAdmin)
