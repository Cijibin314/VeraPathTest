from django.apps import AppConfig


class AnalyticsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'leakfix_mvp.analytics'

    def ready(self):
        import leakfix_mvp.analytics.signals
