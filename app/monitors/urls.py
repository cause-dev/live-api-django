from django.urls import path

from monitors.views import dashboard, api_crud, logs

urlpatterns = [
    path("", dashboard.DashboardView.as_view(), name="dashboard"),
    path(
        "dashboard/poll/", dashboard.DashboardPollView.as_view(), name="dashboard_poll"
    ),
    path("api/<int:pk>/", api_crud.APIDetailsView.as_view(), name="api_detail"),
    path("api/create/", api_crud.AddAPIView.as_view(), name="add_api"),
    path("api/<int:pk>/edit/", api_crud.UpdateAPIView.as_view(), name="edit_api"),
    path(
        "api/<int:pk>/check/", api_crud.MonitorAPIView.as_view(), name="monitor_check"
    ),
    path("api/<int:pk>/row/", api_crud.MonitorRowView.as_view(), name="monitor_row"),
    path(
        "api/<int:pk>/delete/",
        api_crud.MonitorDeleteView.as_view(),
        name="monitor_delete",
    ),
    path("logs/", logs.LogsView.as_view(), name="monitor_logs"),
]
