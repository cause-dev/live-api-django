from datetime import timedelta

from django.shortcuts import render
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from django_htmx.http import trigger_client_event

from config.template_registry import T

from monitors.utils import get_endpoint_stats
from monitors.tasks import check_api_task
from monitors.models import Endpoint
from monitors.forms import EndpointForm


# --- 1. DETAIL VIEW ---
class EndpointView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Endpoint
    template_name = "monitors/endpoint/endpoint.html"

    def test_func(self):
        """Security: Ensure only the owner can view this endpoint."""
        return self.get_object().user == self.request.user

    def get_queryset(self):
        """Optimization: Only look for endpoints belonging to the user."""
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        obj = self.object

        # 1. Get logs from the last 24 hours for the chart
        last_24h = timezone.now() - timedelta(hours=24)
        chart_logs = obj.logs.filter(timestamp__gte=last_24h).order_by("timestamp")

        # 2. Format data for Chart.js
        # We use .strftime to make the timestamps readable in JS
        context["chart_labels"] = [
            log.timestamp.strftime("%H:%M") for log in chart_logs
        ]
        context["chart_data"] = [
            log.latency if log.latency else 0 for log in chart_logs
        ]

        context["uptime_percentage"] = obj.uptime_percentage
        context["avg_latency"] = obj.avg_latency

        return context


class AddEndpointView(LoginRequiredMixin, CreateView):
    model = Endpoint
    form_class = EndpointForm
    template_name = "monitors/endpoint/partials/form.html"
    success_url = reverse_lazy("dashboard")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["label"] = "Add New Endpoint"
        return context

    def form_valid(self, form):
        # 1. Assign data
        form.instance.user = self.request.user
        form.instance.is_online = True

        # 2. Save to DB
        self.object = form.save()

        # 3. HTMX Response
        if self.request.htmx:
            messages.success(
                self.request, f"Endpoint '{self.object.name}' added successfully."
            )

            # Get fresh stats after the save
            context = get_endpoint_stats(self.request.user)

            endpoints = Endpoint.objects.filter(user=self.request.user).order_by(
                "-created_at"
            )
            context["endpoints"] = endpoints

            response = render(
                self.request, "monitors/dashboard/partials/htmx-response.html", context
            )

            return trigger_client_event(response, "modalClose", {})

        return super().form_valid(form)

    def form_invalid(self, form):
        """Handles HTMX form validation errors (e.g. invalid URL)."""
        if self.request.htmx:
            return render(self.request, self.template_name, {"form": form})
        return super().form_invalid(form)


class UpdateEndpointView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Endpoint
    form_class = EndpointForm
    template_name = "monitors/endpoint/partials/form.html"
    success_url = reverse_lazy("dashboard")

    def test_func(self):
        """Security: Ensure only the owner can edit this endpoint."""
        return self.get_object().user == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["label"] = "Update Endpoint"
        return context

    def form_valid(self, form):
        # 1. Save the updated data
        self.object = form.save()

        # 2. HTMX Response
        if self.request.htmx:
            messages.success(
                self.request, f"Endpoint '{self.object.name}' updated successfully."
            )
            # Use the shared helper for accurate stats
            context = get_endpoint_stats(self.request.user)
            endpoints = Endpoint.objects.filter(user=self.request.user).order_by(
                "-created_at"
            )
            context["endpoints"] = endpoints

            response = render(
                self.request, "monitors/dashboard/partials/htmx-response.html", context
            )
            # Trigger the client-side event to close the modal
            return trigger_client_event(response, "modalClose", {})

        return super().form_valid(form)

    def form_invalid(self, form):
        """Handles HTMX form validation errors (e.g. invalid URL)."""
        if self.request.htmx:
            return render(self.request, self.template_name, {"form": form})
        return super().form_invalid(form)


class DeleteEndpointView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Endpoint
    success_url = reverse_lazy("dashboard")

    def test_func(self):
        """Security: Ensure only the owner can delete this endpoint."""
        return self.get_object().user == self.request.user

    def delete(self, request, *args, **kwargs):
        # 1. Perform the deletion
        self.object = self.get_object()
        self.object.delete()

        # 2. HTMX Response
        if request.htmx:
            messages.error(self.request, f"Endpoint '{self.object.name}' deleted.")

            endpoints = Endpoint.objects.filter(user=self.request.user).order_by(
                "-created_at"
            )
            context = get_endpoint_stats(request.user)
            context["endpoints"] = endpoints
            print(context)

            return render(
                request, "monitors/dashboard/partials/htmx-response.html", context
            )

        return super().delete(request, *args, **kwargs)


class EndpointCheckView(
    LoginRequiredMixin, UserPassesTestMixin, SingleObjectMixin, View
):
    model = Endpoint

    def test_func(self):
        return self.get_object().user == self.request.user

    def post(self, request, *args, **kwargs):
        endpoint = self.get_object()

        check_api_task.delay(endpoint.id)

        context = get_endpoint_stats(request.user)
        context["endpoint"] = endpoint
        context["is_checking"] = True

        return render(request, T["LAYOUT"]["HTMX_BASE"], context)


class MonitorRowView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Endpoint
    template_name = T["MONITORS"]["PARTIALS"]["ENDPOINTS"]["ROW"]
    context_object_name = "endpoint"

    def test_func(self):
        return self.get_object().user == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_endpoint_stats(self.request.user))
        return context
