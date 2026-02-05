from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Recipe, MealPlan, UserProfile, Comment
import datetime

# Unregister the default User admin
admin.site.unregister(User)

# Inline for UserProfile
class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'Profile Information'
    fields = ('allergies', 'preferences', 'description')

# Inline for MealPlans
class MealPlanInline(admin.TabularInline):
    model = MealPlan
    extra = 0
    fields = ('date', 'meal_type', 'recipe', 'custom_meal', 'notes')
    readonly_fields = ()
    can_delete = True
    show_change_link = True

# Custom User Admin with full editing capabilities
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline, MealPlanInline)
    
    list_display = ('username', 'email', 'first_name', 'last_name' , 'is_active', 'date_joined')
    list_filter = ( 'is_superuser', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    # Define which fields can be edited
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {
            'fields': ('is_active', 'is_superuser', 'groups', 'user_permissions'),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    # Fields when adding a new user
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
    
    # Make readonly only the date fields
    readonly_fields = ('last_login', 'date_joined')
    
    # Actions
    actions = ['activate_users', 'deactivate_users', 'delete_selected']
    
    def activate_users(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} user(s) activated.')
    activate_users.short_description = "Activate selected users"
    
    def deactivate_users(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} user(s) deactivated.')
    deactivate_users.short_description = "Deactivate selected users"


# Recipe Admin with enhanced editing
@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ('name', 'meal_type', 'created_by', 'prep_time', 'cook_time', 'servings', 'is_popular', 'created_at')
    list_filter = ('meal_type', 'is_popular', 'created_at')
    search_fields = ('name', 'description', 'ingredients')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'meal_type', 'created_by')
        }),
        ('Time & Servings', {
            'fields': ('prep_time', 'cook_time', 'servings')
        }),
        ('Recipe Content', {
            'fields': ('ingredients', 'instructions')
        }),
        ('Additional Info', {
            'fields': ('image_url', 'is_popular', 'popularity_score')
        }),
    )
    
    actions = ['mark_as_popular', 'mark_as_not_popular', 'delete_selected']
    
    def mark_as_popular(self, request, queryset):
        updated = queryset.update(is_popular=True)
        self.message_user(request, f'{updated} recipe(s) marked as popular.')
    mark_as_popular.short_description = "✓ Mark as popular"
    
    def mark_as_not_popular(self, request, queryset):
        updated = queryset.update(is_popular=False)
        self.message_user(request, f'{updated} recipe(s) marked as not popular.')
    mark_as_not_popular.short_description = "✗ Mark as not popular"


# MealPlan Admin with enhanced features
@admin.register(MealPlan)
class MealPlanAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'date', 'meal_type', 'get_meal_name', 'created_at')
    list_filter = ('meal_type', 'date', 'user')
    search_fields = ('user__username', 'recipe__name', 'custom_meal', 'notes')
    date_hierarchy = 'date'
    ordering = ('-date', 'user', 'meal_type')
    
    fieldsets = (
        ('Meal Plan Information', {
            'fields': ('user', 'date', 'meal_type')
        }),
        ('Meal Details', {
            'fields': ('recipe', 'custom_meal', 'notes')
        }),
    )
    
    def get_meal_name(self, obj):
        if obj.recipe:
            return obj.recipe.name
        elif obj.custom_meal:
            return obj.custom_meal
        return "No meal"
    get_meal_name.short_description = 'Meal'
    
    actions = ['delete_selected', 'change_to_breakfast', 'change_to_lunch', 'change_to_dinner', 'change_to_midnight_snack']
    
    def change_to_breakfast(self, request, queryset):
        updated = queryset.update(meal_type='breakfast')
        self.message_user(request, f'{updated} meal(s) changed to Breakfast.')
    change_to_breakfast.short_description = "🍳 Change to Breakfast"
    
    def change_to_lunch(self, request, queryset):
        updated = queryset.update(meal_type='lunch')
        self.message_user(request, f'{updated} meal(s) changed to Lunch.')
    change_to_lunch.short_description = "🍱 Change to Lunch"
    
    def change_to_dinner(self, request, queryset):
        updated = queryset.update(meal_type='dinner')
        self.message_user(request, f'{updated} meal(s) changed to Dinner.')
    change_to_dinner.short_description = "🍽️ Change to Dinner"
    
    def change_to_midnight_snack(self, request, queryset):
        updated = queryset.update(meal_type='midnight_snack')
        self.message_user(request, f'{updated} meal(s) changed to Midnight Snack.')
    change_to_midnight_snack.short_description = "🌙 Change to Midnight Snack"


# UserProfile Admin with direct editing
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_username', 'get_email', 'allergies_preview', 'preferences_preview', 'edit_user_link')
    search_fields = ('user__username', 'user__email', 'allergies', 'preferences')
    list_filter = ('user__date_joined',)
    
    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Dietary Information', {
            'fields': ('allergies', 'preferences', 'description')
        }),
    )
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
    
    def allergies_preview(self, obj):
        return obj.allergies[:50] + '...' if len(obj.allergies) > 50 else obj.allergies or 'None'
    allergies_preview.short_description = 'Allergies'
    
    def preferences_preview(self, obj):
        return obj.preferences[:50] + '...' if len(obj.preferences) > 50 else obj.preferences or 'None'
    preferences_preview.short_description = 'Preferences'
    
    def edit_user_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        url = reverse('admin:auth_user_change', args=[obj.user.id])
        return format_html('<a href="{}">Edit User Account</a>', url)
    edit_user_link.short_description = 'Edit Account'


# Comment Admin
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_preview', 'is_important', 'created_at')
    list_filter = ('is_important', 'created_at', 'user')
    search_fields = ('user__username', 'content')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Comment Information', {
            'fields': ('user', 'content', 'is_important')
        }),
    )
    
    def content_preview(self, obj):
        return obj.content[:75] + '...' if len(obj.content) > 75 else obj.content
    content_preview.short_description = 'Content'
    
    actions = ['mark_as_important', 'mark_as_not_important', 'delete_selected']
    
    def mark_as_important(self, request, queryset):
        updated = queryset.update(is_important=True)
        self.message_user(request, f'{updated} comment(s) marked as important.')
    mark_as_important.short_description = "⭐ Mark as important"
    
    def mark_as_not_important(self, request, queryset):
        updated = queryset.update(is_important=False)
        self.message_user(request, f'{updated} comment(s) marked as not important.')
    mark_as_not_important.short_description = "Remove importance"


# Customize admin site
admin.site.site_header = "🍽️ Meal Planner Administration"
admin.site.site_title = "Meal Planner Admin"
admin.site.index_title = "Welcome to Meal Planner Database Management"