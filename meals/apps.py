from django.apps import AppConfig


class MealsConfig(AppConfig):
    """Configuration for meals app"""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'meals'
    verbose_name = 'Meal Planning'