from django.urls import path
from . import views

urlpatterns = [
    path("health", views.health),
    path("parks/within", views.parks_within),
    path("playgrounds/nearest", views.playgrounds_nearest),
    path("routes/intersecting_park", views.routes_intersecting_park),
    path("routes/within", views.routes_within),
    path("parks/containing", views.park_containing_point),
    path("parks/search", views.parks_search),
    path("playgrounds/search", views.playgrounds_search),
    path("playgrounds", views.playground_create),
    path("playgrounds/<int:pk>", views.playground_update),
    path("playgrounds/<int:pk>/delete", views.playground_delete),
    path("playgrounds/<int:pk>/get", views.playground_get),
    path("access/routes/within", views.accessible_routes_within, name="accessible_routes_within"),
    path("access/issues/near", views.access_issues_near, name="access_issues_near"),
    path("access/issues", views.access_issue_create, name="access_issue_create"),
]
