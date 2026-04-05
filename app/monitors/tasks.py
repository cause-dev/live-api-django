from celery import shared_task
from .models import Monitor
from .services import MonitorService


@shared_task
def check_api_task(api_id):
    """
    Background task to ping a specific monitor.
    """
    try:
        monitor = Monitor.objects.get(id=api_id)
        service = MonitorService(monitor)
        service.run_check()
        return f"Successfully checked {monitor.name}"
    except Monitor.DoesNotExist:
        return f"Monitor with id {api_id} no longer exists."


@shared_task
def check_all_apis_task():
    """
    Background task to ping all monitors.
    """
    active_monitors = Monitor.objects.filter(is_active=True)
    for monitor in active_monitors:
        check_api_task.delay(monitor.id)

    return f"Scheduled checks for {active_monitors.count()} monitors."
