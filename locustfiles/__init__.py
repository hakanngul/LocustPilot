# Auto-import ReportPortal hook for all locustfiles
try:
    import locust_app.core.hooks  # noqa: F401
except ImportError:
    pass
