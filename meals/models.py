from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class UserProfile(models.Model):
    """
    User Profile Model
    Stores user-specific information like allergies and dietary preferences
    One-to-one relationship with Django's User model
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    allergies = models.TextField(
        blank=True, 
        help_text="List any food allergies (e.g., peanuts, shellfish, dairy)"
    )
    preferences = models.TextField(
        blank=True, 
        help_text="Dietary preferences and notes (e.g., vegetarian, low-carb)"
    )
    description = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}'s Profile"


class Recipe(models.Model):
    MEAL_TYPE_CHOICES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('midnight_snack', 'Midnight Snack'),
        ('any', 'Any Meal'),
    ]
    
    name = models.CharField(max_length=200, db_index=True)
    description = models.TextField()
    ingredients = models.TextField(help_text="List ingredients line by line")
    instructions = models.TextField(help_text="Step-by-step cooking instructions")
    prep_time = models.IntegerField(
        help_text="Preparation time in minutes",
        default=0
    )
    cook_time = models.IntegerField(
        help_text="Cooking time in minutes",
        default=0
    )
    servings = models.IntegerField(default=1, help_text="Number of servings")
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPE_CHOICES, default='lunch')
    is_popular = models.BooleanField(
        default=False, 
        help_text="Mark as popular to show on dashboard"
    )
    popularity_score = models.IntegerField(
        default=0, 
        help_text="Higher score = higher ranking"
    )
    image_url = models.URLField(blank=True, null=True, help_text="Recipe image URL")
    created_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='recipes'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Recipe"
        verbose_name_plural = "Recipes"
        ordering = ['-popularity_score', '-created_at']
        indexes = [
            models.Index(fields=['-popularity_score', '-created_at']),
            models.Index(fields=['is_popular']),
        ]

    def __str__(self):
        return self.name
    
    @staticmethod
    def autocomplete_search_fields():
        return ("name__icontains", "description__icontains")

    @property
    def total_time(self):
        """Calculate total cooking time"""
        return self.prep_time + self.cook_time


class MealPlan(models.Model):
    """
    Meal Plan Model
    Stores planned meals for specific dates and meal types
    Each user can have one meal per meal_type per date
    """
    MEAL_TYPES = [
        ('breakfast', 'Breakfast'),
        ('lunch', 'Lunch'),
        ('dinner', 'Dinner'),
        ('midnight_snack', 'Midnight Snack'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='meal_plans')
    date = models.DateField(db_index=True)
    meal_type = models.CharField(max_length=20, choices=MEAL_TYPES, db_index=True)
    recipe = models.ForeignKey(
        Recipe, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True,
        related_name='meal_plans'
    )
    custom_meal = models.CharField(
        max_length=200, 
        blank=True,
        help_text="Custom meal name if not using a recipe"
    )
    notes = models.TextField(blank=True, help_text="Additional notes or modifications")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Meal Plan"
        verbose_name_plural = "Meal Plans"
        unique_together = ['user', 'date', 'meal_type']
        ordering = ['date', 'meal_type']
        indexes = [
            models.Index(fields=['user', 'date']),
            models.Index(fields=['user', 'date', 'meal_type']),
        ]

    def __str__(self):
        meal_name = self.recipe.name if self.recipe else self.custom_meal
        return f"{self.user.username} - {self.date} - {self.get_meal_type_display()}: {meal_name}"

    def clean(self):
        """Validate that either recipe or custom_meal is provided"""
        from django.core.exceptions import ValidationError
        if not self.recipe and not self.custom_meal:
            raise ValidationError("Either recipe or custom meal must be provided")


class Comment(models.Model):
    """
    Comment Model
    Stores user notes about allergies, preferences, and meal planning tips
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    content = models.TextField(help_text="Note content")
    is_important = models.BooleanField(
        default=True,
        help_text="Mark as important to display on dashboard"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Comment"
        verbose_name_plural = "Comments"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['user', 'is_important']),
        ]

    def __str__(self):
        preview = self.content[:50] + '...' if len(self.content) > 50 else self.content
        return f"{self.user.username} - {preview}"