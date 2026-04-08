from django.urls import reverse_lazy
from django.shortcuts import render
from django.views import View
from django.db.models import Avg
from django.views.generic import TemplateView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.edit import DeleteView
from django.views.generic.detail import SingleObjectMixin, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django_htmx.http import trigger_client_event
from .models import Monitor, MonitorLog
from .forms import AddAPIForm
from .utils import get_monitor_stats
from .tasks import check_api_task

# Create your views here.


class DashboardView(LoginRequiredMixin, ListView):
    model = Monitor
    template_name = "monitors/dashboard.html"
    context_object_name = "monitors"

    def get_queryset(self):
        # Always filter by current user and newest first
        return Monitor.objects.filter(user=self.request.user).order_by("-created_at")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Merges our stats helper into the template context
        context.update(get_monitor_stats(self.request.user))
        context["base_template"] = (
            "partials/content_base.html" if self.request.htmx else "base.html"
        )
        return context


class DashboardPollView(LoginRequiredMixin, TemplateView):
    template_name = "monitors/partials/dashboard_poll.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["monitors"] = Monitor.objects.filter(user=self.request.user).order_by(
            "-created_at"
        )
        context.update(get_monitor_stats(self.request.user))
        return context


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

        monitor = self.get_object()
        context["recent_logs"] = monitor.logs.all()[:10]  # Show last 10 logs

        avg_latency = monitor.logs.aggregate(Avg("latency"))["latency__avg"]
        context["avg_latency"] = avg_latency if avg_latency is not None else 0

        total_logs = monitor.logs.count()
        if total_logs > 0:
            online_logs = monitor.logs.filter(is_online=True).count()
            context["uptime_percentage"] = round((online_logs / total_logs) * 100, 1)
        else:
            context["uptime_percentage"] = 0.0

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


class LogsView(LoginRequiredMixin, ListView):
    model = MonitorLog
    template_name = "monitors/logs.html"
    context_object_name = "logs"
    paginate_by = 25

    def get_queryset(self):
        qs = (
            MonitorLog.objects.filter(monitor__user=self.request.user)
            .select_related("monitor")
            .order_by("-timestamp")
        )

        monitor_id = self.request.GET.get("monitor_id")
        if monitor_id:
            qs = qs.filter(monitor_id=monitor_id)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_monitors"] = Monitor.objects.filter(user=self.request.user)
        context["base_template"] = (
            "partials/content_base.html" if self.request.htmx else "base.html"
        )
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.htmx:
            if self.request.GET.get("monitor_id"):
                # If a specific monitor is selected, we only update the table body
                return render(
                    self.request, "monitors/partials/log_table_body.html", context
                )

        return super().render_to_response(context, **response_kwargs)
