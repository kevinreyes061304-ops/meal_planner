from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.forms import UserCreationForm
from django.utils import timezone
from datetime import timedelta, date
from django.contrib import messages
from django.db.models import Q
from .models import MealPlan, Recipe, UserProfile, Comment
from .forms import (WeeklyMealPlanFormSet, CommentForm, UserProfileForm, 
                    UserUpdateForm, CustomPasswordChangeForm, CustomRecipeForm)


def landing(request):
    """
    Public Landing Page
    Shows welcome page for non-authenticated users
    Redirects to dashboard if user is already logged in
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    return render(request, 'meals/landing.html')


@login_required
def dashboard(request):
    """
    Dashboard View - Landing page
    Shows today's meals, popular recipes, and important notes
    """
    # Always use the actual current date
    today = timezone.now().date()
    
    # Get or create user profile
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    # Get today's meals for all meal types WITH recipe data
    meal_types = ['breakfast', 'lunch', 'dinner', 'midnight_snack']
    meals = {}
    
    for meal_type in meal_types:
        meal = MealPlan.objects.filter(
            user=request.user,
            date=today,
            meal_type=meal_type
        ).select_related('recipe').first()
        meals[meal_type] = meal
    
    # Get popular recipes (top 6)
    popular_recipes = Recipe.objects.filter(is_popular=True)[:6]
    
    # Get recent important comments (top 5)
    recent_comments = Comment.objects.filter(
        user=request.user,
        is_important=True
    ).order_by('-created_at')[:5]  # Added ordering by most recent
    
    context = {
        'today': today,
        'meals': meals,
        'popular_recipes': popular_recipes,
        'recent_comments': recent_comments,
        'user_profile': user_profile,
    }
    
    return render(request, 'meals/dashboard.html', context)


@login_required
def edit_weekly_plan(request):
    """
    Weekly Plan View
    Edit entire week's meal plan (Monday-Sunday)
    Always shows the current week
    """
    # Always use the actual current date
    today = timezone.now().date()
    
    # Get Monday of current week
    start_of_week = today - timedelta(days=today.weekday())
    
    # Generate list of 7 dates (Monday to Sunday)
    week_dates = [start_of_week + timedelta(days=i) for i in range(7)]
    
    if request.method == 'POST':
        saved_count = 0
        deleted_count = 0
        meal_types = ['breakfast', 'lunch', 'dinner', 'midnight_snack']
        
        # Process each date and meal type combination
        for date in week_dates:
            for meal_type in meal_types:
                # Create the field name prefix that matches the form
                prefix = f'{date.isoformat()}_{meal_type}'
                
                # Get values from POST data
                recipe_id = request.POST.get(f'{prefix}-recipe', '')
                custom_meal = request.POST.get(f'{prefix}-custom_meal', '').strip()
                notes = request.POST.get(f'{prefix}-notes', '').strip()
                
                # Determine if we should save or delete
                recipe_obj = None
                if recipe_id and recipe_id != '':
                    try:
                        recipe_obj = Recipe.objects.get(id=int(recipe_id))
                    except (ValueError, Recipe.DoesNotExist):
                        pass
                
                # If both recipe and custom_meal are empty, delete the meal plan
                if not recipe_obj and not custom_meal:
                    deleted = MealPlan.objects.filter(
                        user=request.user,
                        date=date,
                        meal_type=meal_type
                    ).delete()
                    if deleted[0] > 0:
                        deleted_count += 1
                else:
                    # Create or update meal plan
                    meal_plan, created = MealPlan.objects.update_or_create(
                        user=request.user,
                        date=date,
                        meal_type=meal_type,
                        defaults={
                            'recipe': recipe_obj,
                            'custom_meal': custom_meal,
                            'notes': notes,
                        }
                    )
                    saved_count += 1
        
        # Create success message
        if saved_count > 0 or deleted_count > 0:
            message = f'Weekly meal plan updated! {saved_count} meals saved'
            if deleted_count > 0:
                message += f', {deleted_count} removed'
            messages.success(request, message)
        else:
            messages.info(request, 'No changes were made to your meal plan.')
        
        return redirect('dashboard')
    
    # GET request - load existing data
    formset = WeeklyMealPlanFormSet(
        user=request.user,
        dates=week_dates
    )
    
    # Get all recipes - custom recipes first, then standard recipes
    custom_recipes = Recipe.objects.filter(created_by=request.user).order_by('name')
    standard_recipes = Recipe.objects.filter(created_by__isnull=True).order_by('name')
    recipes = list(custom_recipes) + list(standard_recipes)
    
    # Get all recipes for the dropdowns
    recipes = Recipe.objects.all()
    
    # Get existing meal plans for the week
    existing_meals = MealPlan.objects.filter(
        user=request.user,
        date__in=week_dates
    ).select_related('recipe')
    
    # Create a dictionary for easy lookup: "date|meal_type" -> meal_plan
    meals_dict = {}
    for meal in existing_meals:
        key = f"{meal.date}|{meal.meal_type}"
        meals_dict[key] = {
            'recipe_id': meal.recipe.id if meal.recipe else None,
            'custom_meal': meal.custom_meal or '',
            'notes': meal.notes or '',
        }
    
    context = {
        'formset': formset,
        'week_dates': week_dates,
        'start_of_week': start_of_week,
        'today': today,  # Add today to context
        'recipes': recipes,
        'meals_dict': meals_dict,
    }
    
    return render(request, 'meals/edit_weekly_plan.html', context)


@login_required
def add_comment(request):
    """
    Add Comment View
    Create new important note/comment
    """
    if request.method == 'POST':
        form = CommentForm(request.POST)
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.user = request.user
            comment.save()
            
            messages.success(
                request,
                'Your note has been added successfully!'
            )
            return redirect('dashboard')
    else:
        form = CommentForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'meals/add_comment.html', context)


@login_required
def edit_profile(request):
    """
    Edit Profile View
    Update user info, profile, allergies and preferences
    """
    user_profile, created = UserProfile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Check which form was submitted
        if 'update_info' in request.POST:
            user_form = UserUpdateForm(request.POST, instance=request.user)
            profile_form = UserProfileForm(request.POST, instance=user_profile)
            
            if user_form.is_valid() and profile_form.is_valid():
                user_form.save()
                profile_form.save()
                messages.success(request, 'Your profile has been updated successfully!')
                return redirect('edit_profile')
                
        elif 'change_password' in request.POST:
            password_form = CustomPasswordChangeForm(request.user, request.POST)
            
            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                messages.success(request, 'Your password has been changed successfully!')
                return redirect('edit_profile')
            else:
                messages.error(request, 'Please correct the errors below.')
    else:
        user_form = UserUpdateForm(instance=request.user)
        profile_form = UserProfileForm(instance=user_profile)
        password_form = CustomPasswordChangeForm(request.user)
    
    context = {
        'user_form': user_form,
        'profile_form': profile_form,
        'password_form': password_form,
    }
    
    return render(request, 'meals/edit_profile.html', context)


@login_required
def recipe_detail(request, recipe_id):
    """
    Recipe Detail View
    Display complete recipe information
    """
    recipe = get_object_or_404(Recipe, id=recipe_id)
    
    context = {
        'recipe': recipe,
    }
    
    return render(request, 'meals/recipe_detail.html', context)


@login_required
def add_meal_to_plan(request, recipe_id):
    """
    Add Meal to Plan View
    Quick add recipe to today's meal plan
    """
    recipe = get_object_or_404(Recipe, id=recipe_id)
    today = timezone.now().date()  # Always use current date
    
    if request.method == 'POST':
        meal_type = request.POST.get('meal_type')
        
        if meal_type in dict(MealPlan.MEAL_TYPES):
            MealPlan.objects.update_or_create(
                user=request.user,
                date=today,
                meal_type=meal_type,
                defaults={'recipe': recipe}
            )
            
            messages.success(
                request,
                f'{recipe.name} has been added to your {meal_type}!'
            )
            return redirect('dashboard')
        else:
            messages.error(request, 'Invalid meal type selected.')
    
    return redirect('recipe_detail', recipe_id=recipe_id)


def register(request):
    """
    Registration View
    Allow new users to create an account
    """
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Automatically log in after registration
            messages.success(request, 'Welcome! Your account has been created.')
            return redirect('dashboard')
    else:
        form = UserCreationForm()
    
    return render(request, 'registration/register.html', {'form': form})


def logout_view(request):
    """
    Custom logout view that handles both GET and POST
    """
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('landing')

@login_required
def delete_account(request):
    """
    Delete Account View
    Allow users to permanently delete their account
    """
    if request.method == 'POST':
        password = request.POST.get('password')
        
        # Verify password before deletion
        if request.user.check_password(password):
            username = request.user.username
            request.user.delete()
            messages.success(request, f'Your account "{username}" has been permanently deleted.')
            return redirect('landing')
        else:
            messages.error(request, 'Incorrect password. Account was not deleted.')
            return redirect('edit_profile')
    
    # GET request - show confirmation page
    return render(request, 'meals/delete_account.html')

@login_required
def delete_meal(request, date, meal_type):
    """
    Delete a single meal from the plan
    """
    print(f"DEBUG: delete_meal called - Method: {request.method}, Date: {date}, Meal Type: {meal_type}")
    
    if request.method == 'POST':
        try:
            from datetime import datetime
            meal_date = datetime.strptime(date, '%Y-%m-%d').date()
            
            print(f"DEBUG: Looking for meal - User: {request.user}, Date: {meal_date}, Type: {meal_type}")
            
            meal_to_delete = MealPlan.objects.filter(
                user=request.user,
                date=meal_date,
                meal_type=meal_type
            ).first()
            
            print(f"DEBUG: Found meal: {meal_to_delete}")
            
            deleted = MealPlan.objects.filter(
                user=request.user,
                date=meal_date,
                meal_type=meal_type
            ).delete()
            
            print(f"DEBUG: Deleted count: {deleted}")
            
            if deleted[0] > 0:
                messages.success(request, f'Meal deleted successfully!')
            else:
                messages.info(request, 'No meal found to delete.')
        except Exception as e:
            print(f"DEBUG: Error - {str(e)}")
            messages.error(request, f'Error deleting meal: {str(e)}')
    
    return redirect('edit_weekly_plan')


@login_required
def clear_week(request):
    """
    Clear all meals for the current week
    """
    print(f"DEBUG: clear_week called - Method: {request.method}")
    
    if request.method == 'POST':
        today = timezone.now().date()
        start_of_week = today - timedelta(days=today.weekday())
        week_dates = [start_of_week + timedelta(days=i) for i in range(7)]
        
        print(f"DEBUG: Week dates: {week_dates}")
        
        meals = MealPlan.objects.filter(
            user=request.user,
            date__in=week_dates
        )
        
        print(f"DEBUG: Found {meals.count()} meals to delete")
        
        deleted = meals.delete()
        
        print(f"DEBUG: Deleted: {deleted}")
        
        if deleted[0] > 0:
            messages.success(request, f'All meals cleared! {deleted[0]} meals removed.')
        else:
            messages.info(request, 'No meals found to clear.')
    
    return redirect('edit_weekly_plan')


@login_required
def delete_day_meals(request, date):
    """
    Delete all meals for a specific day
    """
    print(f"DEBUG: delete_day_meals called - Method: {request.method}, Date: {date}")
    
    if request.method == 'POST':
        try:
            from datetime import datetime
            meal_date = datetime.strptime(date, '%Y-%m-%d').date()
            
            print(f"DEBUG: Looking for meals on date: {meal_date} for user: {request.user}")
            
            meals = MealPlan.objects.filter(
                user=request.user,
                date=meal_date
            )
            
            print(f"DEBUG: Found {meals.count()} meals to delete")
            for meal in meals:
                print(f"  - {meal.meal_type}: {meal.recipe or meal.custom_meal}")
            
            deleted = meals.delete()
            
            print(f"DEBUG: Deleted: {deleted}")
            
            if deleted[0] > 0:
                messages.success(request, f'All meals for {meal_date.strftime("%A, %B %d")} deleted! ({deleted[0]} meals)')
            else:
                messages.info(request, 'No meals found to delete.')
        except Exception as e:
            print(f"DEBUG: Error - {str(e)}")
            import traceback
            traceback.print_exc()
            messages.error(request, f'Error deleting meals: {str(e)}')
    else:
        print(f"DEBUG: Not POST method, got: {request.method}")
    
    return redirect('edit_weekly_plan')

@login_required
def add_custom_recipe(request):
    """
    Add Custom Recipe View
    Allow users to create their own recipes
    """
    if request.method == 'POST':
        form = CustomRecipeForm(request.POST)
        if form.is_valid():
            recipe = form.save(commit=False)
            recipe.created_by = request.user
            recipe.save()
            messages.success(request, f'Recipe "{recipe.name}" has been added!')
            return redirect('my_recipes')
    else:
        form = CustomRecipeForm()
    
    return render(request, 'meals/add_custom_recipe.html', {'form': form})


@login_required
def my_recipes(request):
    
    custom_recipes = Recipe.objects.filter(created_by=request.user)
    
    # Filter by meal type if specified
    meal_type = request.GET.get('meal_type')
    if meal_type and meal_type != 'all':
        custom_recipes = custom_recipes.filter(meal_type=meal_type)
    
    return render(request, 'meals/my_recipes.html', {
        'custom_recipes': custom_recipes
    })

@login_required
def delete_custom_recipe(request, recipe_id):
    """
    Delete Custom Recipe View
    """
    recipe = get_object_or_404(Recipe, id=recipe_id, created_by=request.user)
    
    if request.method == 'POST':
        recipe_name = recipe.name
        recipe.delete()
        messages.success(request, f'Recipe "{recipe_name}" has been deleted.')
    
    return redirect('my_recipes')