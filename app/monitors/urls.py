from django.urls import path

from monitors import views

urlpatterns = [
    path("", views.DashboardView.as_view(), name="dashboard"),
    path("dashboard/poll/", views.DashboardPollView.as_view(), name="dashboard_poll"),
    path("endpoint/<int:pk>/", views.EndpointView.as_view(), name="endpoint"),
    path("endpoint/create/", views.AddEndpointView.as_view(), name="add_endpoint"),
    path(
        "endpoint/<int:pk>/edit/",
        views.UpdateEndpointView.as_view(),
        name="edit_endpoint",
    ),
    path(
        "endpoint/<int:pk>/check/",
        views.MonitorAPIView.as_view(),
        name="check_endpoint",
    ),
    path("endpoint/<int:pk>/row/", views.MonitorRowView.as_view(), name="endpoint_row"),
    path(
        "endpoint/<int:pk>/delete/",
        views.DeleteEndpointView.as_view(),
        name="delete_endpoint",
    ),
    path("logs/", views.LogsView.as_view(), name="endpoint_logs"),
]
