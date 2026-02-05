from django.urls import path
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('weekly-plan/', views.edit_weekly_plan, name='edit_weekly_plan'),
    path('weekly-plan/clear/', views.clear_week, name='clear_week'),
    path('weekly-plan/delete-day/<str:date>/', views.delete_day_meals, name='delete_day_meals'),
    path('weekly-plan/delete-meal/<str:date>/<str:meal_type>/', views.delete_meal, name='delete_meal'),
    path('add-comment/', views.add_comment, name='add_comment'),
    path('profile/', views.edit_profile, name='edit_profile'),
    path('profile/delete/', views.delete_account, name='delete_account'),
    path('recipes/', views.my_recipes, name='my_recipes'),  # ADD
    path('recipes/add/', views.add_custom_recipe, name='add_custom_recipe'),  # ADD
    path('recipes/delete/<int:recipe_id>/', views.delete_custom_recipe, name='delete_custom_recipe'),  # ADD
    path('recipe/<int:recipe_id>/', views.recipe_detail, name='recipe_detail'),
    path('recipe/<int:recipe_id>/add/', views.add_meal_to_plan, name='add_meal_to_plan'),
]