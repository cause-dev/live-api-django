from .template_registry import T


def global_templates(request):
    return {"T": T}
