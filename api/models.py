from django.db import models


class WalkingRoute(models.Model):
    """
    Read-only view of the walking_routes table in Postgres.
    We map only the non-geometry fields we care about.
    Geometry stays handled via raw SQL + PostGIS.
    """
    id = models.IntegerField(primary_key=True)      # existing PK in DB
    name = models.CharField(max_length=255, blank=True, null=True)
    source = models.CharField(max_length=50, blank=True, null=True)
    surface = models.CharField(max_length=50, blank=True, null=True)
    smoothness = models.CharField(max_length=50, blank=True, null=True)
    is_accessible = models.BooleanField(null=True)  # derived accessibility flag

    class Meta:
        managed = False               # IMPORTANT: Django does NOT create/alter this table
        db_table = 'walking_routes'   # exact table name in Postgres

    def __str__(self):
        return self.name or f"Route {self.id}"


class AccessIssue(models.Model):
    """
    User-reported accessibility issues linked to a walking route.
    This is a normal Django-managed table for CA2.
    """
    route = models.ForeignKey(
        WalkingRoute,
        on_delete=models.CASCADE,
        db_column='route_id',     # FK column name in DB
        related_name='issues'
    )
    issue_type = models.CharField(
        max_length=100,
        help_text="Short code/label, e.g. 'blocked_ramp', 'broken_pavement'"
    )
    description = models.TextField(
        blank=True,
        help_text="Optional free-text description of the issue"
    )
    lat = models.FloatField(
        help_text="Latitude (WGS84)"
    )
    lng = models.FloatField(
        help_text="Longitude (WGS84)"
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        db_table = 'access_issues'    # nice clean table name
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.issue_type} on route {self.route_id} @ ({self.lat:.5f}, {self.lng:.5f})"
