from django.contrib import admin
from .models import WalkingRoute, AccessIssue


@admin.register(WalkingRoute)
class WalkingRouteAdmin(admin.ModelAdmin):
    """
    Read-only admin view for walking_routes.
    We don't let people add/delete here because it's managed by imports.
    """
    list_display = ('id', 'name', 'source', 'surface', 'smoothness', 'is_accessible')
    list_filter = ('source', 'surface', 'smoothness', 'is_accessible')
    search_fields = ('name',)

    def has_add_permission(self, request):
        return False  # prevent manual creation

    def has_delete_permission(self, request, obj=None):
        return False  # prevent deletion


@admin.register(AccessIssue)
class AccessIssueAdmin(admin.ModelAdmin):
    """
    Full CRUD for user-reported accessibility issues.
    """
    list_display = ('id', 'route', 'issue_type', 'created_at', 'lat', 'lng')
    list_filter = ('issue_type', 'created_at')
    search_fields = ('description', 'route__name')
    readonly_fields = ('created_at',)
