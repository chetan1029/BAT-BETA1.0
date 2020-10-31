"""
bat's core URL Configuration.
"""

from django.urls import path

from bat.core.views import TestView

app_name = "core"

urlpatterns = [
    path('test/', TestView.as_view()),
]
