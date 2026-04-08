"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from monitors import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("monitor/poll/", views.DashboardPollView.as_view(), name="dashboard_poll"),
    path("monitor/<int:pk>/", views.APIDetailsView.as_view(), name="monitor_detail"),
    path("monitor/create/", views.AddAPIView.as_view(), name="add_api"),
    path("monitor/<int:pk>/edit/", views.UpdateAPIView.as_view(), name="edit_api"),
    path(
        "monitor/<int:pk>/check/", views.MonitorAPIView.as_view(), name="monitor_check"
    ),
    path("monitor/<int:pk>/row/", views.MonitorRowView.as_view(), name="monitor_row"),
    path(
        "monitor/<int:pk>/delete/",
        views.MonitorDeleteView.as_view(),
        name="monitor_delete",
    ),
    path("logs/", views.LogsView.as_view(), name="monitor_logs"),
    path("user/", include("user.urls")),
]
