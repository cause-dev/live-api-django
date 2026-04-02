from django.urls import reverse_lazy
from django.shortcuts import render
from django.views.generic.list import ListView
from django.views.generic.edit import DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Monitor

# Create your views here.


class DashboardView(ListView):
    template_name = "monitors/dashboard.html"
    model = Monitor
    context_object_name = "monitors"

    def get_queryset(self):
        return Monitor.objects.filter(user=self.request.user).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_monitors = self.get_queryset()

        # Add stats to the context
        context["total_count"] = user_monitors.count()
        context["online_count"] = user_monitors.filter(
            is_online=True, is_active=True
        ).count()
        context["offline_count"] = user_monitors.filter(
            is_online=False, is_active=True
        ).count()
        return context


class MonitorDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Monitor
    success_url = reverse_lazy("dashboard")

    def test_func(self):
        monitor = self.get_object()
        return monitor.user == self.request.user

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()

        if request.htmx:
            user_monitors = Monitor.objects.filter(user=request.user)
            context = {
                "total_count": user_monitors.count(),
                "online_count": user_monitors.filter(
                    is_online=True, is_active=True
                ).count(),
                "offline_count": user_monitors.filter(
                    is_online=False, is_active=True
                ).count(),
            }
            return render(request, "monitors/partials/stats.html", context)

        return super().delete(request, *args, **kwargs)
