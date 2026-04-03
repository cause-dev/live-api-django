from django.urls import reverse_lazy
from django.shortcuts import render
from django.views import View
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView
from django.views.generic.edit import DeleteView
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django_htmx.http import trigger_client_event
from .models import Monitor
from .forms import AddAPIForm
from .utils import get_monitor_stats
from .services import MonitorService

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

        service = MonitorService(monitor)

        updated_monitor = service.run_check()

        context = get_monitor_stats(request.user)
        context["monitor"] = updated_monitor

        return render(
            request, "monitors/partials/update_monitor_response.html", context
        )
