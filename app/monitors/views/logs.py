from django.shortcuts import render
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView

from config.template_registry import T
from monitors.models import Endpoint, EndpointLog


class LogsView(LoginRequiredMixin, ListView):
    model = EndpointLog
    template_name = T["MONITORS"]["LOGS"]
    paginate_by = 25

    def get_queryset(self):
        qs = (
            EndpointLog.objects.filter(endpoint__user=self.request.user)
            .select_related("endpoint")
            .order_by("-timestamp")
        )

        endpoint_id = self.request.GET.get("endpoint_id")
        if endpoint_id:
            qs = qs.filter(endpoint_id=endpoint_id)

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["user_endpoints"] = Endpoint.objects.filter(user=self.request.user)
        context["base_template"] = (
            T["LAYOUT"]["HTMX_BASE"] if self.request.htmx else T["LAYOUT"]["BASE"]
        )
        return context

    def render_to_response(self, context, **response_kwargs):
        if self.request.htmx:
            if self.request.GET.get("endpoint_id"):
                # If a specific endpoint is selected, we only update the table body
                return render(
                    self.request, "monitors/partials/log_table_body.html", context
                )

        return super().render_to_response(context, **response_kwargs)
