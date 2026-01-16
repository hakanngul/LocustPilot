# Auto-import ReportPortal hook for all locustfiles
try:
    import app.core.hooks  # noqa: F401
except ImportError:
    pass
