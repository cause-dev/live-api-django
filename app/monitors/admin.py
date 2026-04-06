from django.contrib import admin
from .models import Monitor, MonitorLog

# Register your models here.


@admin.register(Monitor)
class MonitorAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "url", "expected_status_code", "created_at")
    list_filter = ("expected_status_code", "created_at")
    search_fields = ("name", "url")
    ordering = ("-created_at",)


@admin.register(MonitorLog)
class MonitorLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "monitor",
        "latency",
        "status_code",
        "is_online",
        "timestamp",
        "error_message",
    )
    list_filter = ("status_code", "timestamp")
    search_fields = ("monitor",)
    ordering = ("-timestamp",)
