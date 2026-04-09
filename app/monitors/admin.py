from django.contrib import admin
from .models import Endpoint, EndpointLog

# Register your models here.


@admin.register(Endpoint)
class EndpointAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "url", "expected_status_code", "created_at")
    list_filter = ("expected_status_code", "created_at")
    search_fields = ("name", "url")
    ordering = ("-created_at",)


@admin.register(EndpointLog)
class EndpointLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "endpoint",
        "latency",
        "status_code",
        "is_online",
        "timestamp",
        "error_message",
    )
    list_filter = ("status_code", "timestamp")
    search_fields = ("endpoint",)
    ordering = ("-timestamp",)
