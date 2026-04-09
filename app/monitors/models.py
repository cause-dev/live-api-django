from django.db import models
from django.db.models import Avg
from django.contrib.auth.models import User

# Create your models here.


class Endpoint(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE, related_name="endpoints")
    name = models.CharField(max_length=100)
    url = models.URLField()
    expected_status_code = models.PositiveIntegerField(default=200)
    is_active = models.BooleanField(default=True)
    last_checked = models.DateTimeField(null=True, blank=True)
    is_online = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.url})"

    @property
    def uptime_percentage(self):
        total = self.logs.count()
        if total == 0:
            return 0
        online = self.logs.filter(is_online=True).count()
        return round((online / total) * 100, 1)

    @property
    def avg_latency(self):
        avg = self.logs.aggregate(Avg("latency"))["latency__avg"]
        return round(avg, 3) if avg else 0


class EndpointLog(models.Model):
    endpoint = models.ForeignKey(
        to=Endpoint, on_delete=models.CASCADE, related_name="logs"
    )
    status_code = models.PositiveBigIntegerField(null=True, blank=True)
    latency = models.FloatField(null=True, blank=True)
    is_online = models.BooleanField()
    error_message = models.TextField(max_length=1000, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["timestamp"]),
        ]

    def __str__(self):
        return f"{self.monitor.name} - {self.status_code} at {self.timestamp}"
