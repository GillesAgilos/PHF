from django.apps import AppConfig

class PhfConfig(AppConfig):
    name = 'phf'

    def ready(self):
        import phf.signals