from django.urls import path
from .views_frontend import home

urlpatterns = [
    path('', home),
]
