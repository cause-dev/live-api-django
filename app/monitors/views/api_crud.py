from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone
from django.urls import reverse_lazy
from django.db.models import Avg
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views import View
from django.views.generic.detail import DetailView, SingleObjectMixin
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from django_htmx.http import trigger_client_event

from monitors.utils import get_monitor_stats
from monitors.tasks import check_api_task
from monitors.models import Monitor
from monitors.forms import AddAPIForm


class APIDetailsView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Monitor
    template_name = "monitors/api_details.html"
    context_object_name = "monitor"

    def test_func(self):
        """Security: Ensure only the owner can view this monitor."""
        return self.get_object().user == self.request.user

    def get_queryset(self):
        """Optimization: Only look for monitors belonging to the user."""
        return super().get_queryset().filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        monitor = self.object

        # 1. Get logs from the last 24 hours for the chart
        last_24h = timezone.now() - timedelta(hours=24)
        chart_logs = monitor.logs.filter(timestamp__gte=last_24h).order_by("timestamp")

        # 2. Format data for Chart.js
        # We use .strftime to make the timestamps readable in JS
        context["chart_labels"] = [
            log.timestamp.strftime("%H:%M") for log in chart_logs
        ]
        context["chart_data"] = [
            log.latency if log.latency else 0 for log in chart_logs
        ]

        # 3. Calculate Uptime %
        total_logs = monitor.logs.count()
        if total_logs > 0:
            online_logs = monitor.logs.filter(is_online=True).count()
            context["uptime_percentage"] = round((online_logs / total_logs) * 100, 1)
        else:
            context["uptime_percentage"] = 0

        # 4. Average Latency
        avg = monitor.logs.aggregate(Avg("latency"))["latency__avg"]
        context["avg_latency"] = round(avg, 3) if avg else 0

        context["base_template"] = (
            "partials/content_base.html" if self.request.htmx else "base.html"
        )

        return context


class AddAPIView(LoginRequiredMixin, CreateView):
    model = Monitor
    form_class = AddAPIForm
    template_name = "monitors/partials/add_api_form.html"
    success_url = reverse_lazy("dashboard")

    def form_valid(self, form):
        # 1. Assign data
        form.instance.user = self.request.user
        form.instance.is_online = True

        # 2. Save to DB
        self.object = form.save()

        # 3. HTMX Response
        if self.request.htmx:
            # Get fresh stats after the save
            context = get_monitor_stats(self.request.user)
            # Add the new monitor object to context for the row partial
            context["monitor"] = self.object

            response = render(
                self.request, "monitors/partials/save_monitor_response.html", context
            )
            return trigger_client_event(
                response,
                "monitorAdded",
                {"message": f"Monitor '{self.object.name}' added."},
            )

        return super().form_valid(form)

    def form_invalid(self, form):
        """Handles HTMX form validation errors (e.g. invalid URL)."""
        if self.request.htmx:
            return render(self.request, self.template_name, {"form": form})
        return super().form_invalid(form)


class UpdateAPIView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Monitor
    form_class = AddAPIForm
    template_name = "monitors/partials/edit_api_form.html"
    success_url = reverse_lazy("dashboard")

    def test_func(self):
        """Security: Ensure only the owner can edit this monitor."""
        return self.get_object().user == self.request.user

    def form_valid(self, form):
        # 1. Save the updated data
        self.object = form.save()

        # 2. HTMX Response
        if self.request.htmx:
            # Use the shared helper for accurate stats
            context = get_monitor_stats(self.request.user)
            context["monitor"] = self.object  # Pass the updated object

            response = render(
                self.request, "monitors/partials/update_monitor_response.html", context
            )
            # Trigger the client-side event to close the modal
            return trigger_client_event(
                response,
                "monitorUpdated",
                {"message": f"Monitor '{self.object.name}' updated."},
            )

        return super().form_valid(form)

    def form_invalid(self, form):
        """Handles HTMX form validation errors (e.g. invalid URL)."""
        if self.request.htmx:
            return render(self.request, self.template_name, {"form": form})
        return super().form_invalid(form)


class MonitorDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
    model = Monitor
    success_url = reverse_lazy("dashboard")

    def test_func(self):
        """Security: Ensure only the owner can delete this monitor."""
        return self.get_object().user == self.request.user

    def delete(self, request, *args, **kwargs):
        # 1. Perform the deletion
        self.object = self.get_object()
        self.object.delete()

        # 2. HTMX Response
        if request.htmx:
            context = get_monitor_stats(request.user)

            return render(request, "monitors/partials/stats.html", context)

        return super().delete(request, *args, **kwargs)


class MonitorAPIView(LoginRequiredMixin, UserPassesTestMixin, SingleObjectMixin, View):
    model = Monitor

    def test_func(self):
        return self.get_object().user == self.request.user

    def post(self, request, *args, **kwargs):
        monitor = self.get_object()

        check_api_task.delay(monitor.id)

        context = get_monitor_stats(request.user)
        context["monitor"] = monitor
        context["is_checking"] = True

        return render(
            request, "monitors/partials/update_monitor_response.html", context
        )


class MonitorRowView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    model = Monitor
    template_name = "monitors/partials/update_monitor_response.html"
    context_object_name = "monitor"

    def test_func(self):
        return self.get_object().user == self.request.user

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update(get_monitor_stats(self.request.user))
        return context
