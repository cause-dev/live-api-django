from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView

from monitors.models import Monitor, MonitorLog


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
