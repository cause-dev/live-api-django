from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView
from django.views.generic import TemplateView

from config.template_registry import T
from monitors.utils import get_endpoint_stats
from monitors.models import Endpoint


class DashboardView(LoginRequiredMixin, ListView):
    model = Endpoint
    template_name = T["MONITORS"]["DASHBOARD"]

    def get_queryset(self):
        # Always filter by current user and newest first
        return Endpoint.objects.filter(user=self.request.user).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Merges our stats helper into the template context
        context.update(get_endpoint_stats(self.request.user))
        context["base_template"] = (
            T["LAYOUT"]["HTMX_BASE"] if self.request.htmx else T["LAYOUT"]["BASE"]
        )
        return context


class DashboardPollView(LoginRequiredMixin, TemplateView):
    template_name = T["MONITORS"]["PARTIALS"]["HTMX_RESPONSE"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["endpoints"] = Endpoint.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )
        context.update(get_endpoint_stats(self.request.user))

        return context
