# --- MONITORS APP ---
M_DIR = "monitors"
MONITORS = {
    "DASHBOARD": f"{M_DIR}/dashboard.html",
    "DETAILS": f"{M_DIR}/endpoint.html",
    "LOGS": f"{M_DIR}/logs.html",
    "PARTIALS": {
        "STATS": "partials/dashboard/stats.html",
        "HTMX_RESPONSE": "partials/dashboard/htmx-response.html",
        "ROW": f"{M_DIR}/partials/monitor_row.html",
        "LIST": f"{M_DIR}/partials/monitor_list.html",
        "CONTENT": f"{M_DIR}/partials/dashboard_content.html",
        "ADD_FORM": f"{M_DIR}/partials/add_endpoint_form.html",
        "HEADER": "partials/dashboard/header.html",
        "POLL": "partials/dashboard/poll.html",
        "ENDPOINTS": {
            "LIST": "partials/endpoints/list.html",
            "ROW": "partials/endpoints/endpoint.html",
        },
    },
}

# --- USERS APP (Future proofing) ---
U_DIR = "user"
USERS = {
    "LOGIN": f"{U_DIR}/login.html",
    "PROFILE": f"{U_DIR}/profile.html",
}

LAYOUT = {
    "BASE": "base.html",
    "HTMX_BASE": "partials/htmx_base.html",
    "PARTIALS": {
        "BREADCRUMBS": "partials/breadcrumbs.html",
    },
}

# The Global Registry
T = {
    "MONITORS": MONITORS,
    "USERS": USERS,
    "LAYOUT": LAYOUT,
}
