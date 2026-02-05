from django import forms
from django.forms import formset_factory, BaseFormSet
from .models import MealPlan, Comment, UserProfile, Recipe
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth.models import User


class MealPlanForm(forms.ModelForm):
    """Form for creating/editing a single meal plan"""
    
    class Meta:
        model = MealPlan
        fields = ['recipe', 'custom_meal', 'notes']
        widgets = {
            'recipe': forms.Select(attrs={
                'class': 'form-control',
                'placeholder': 'Select a recipe'
            }),
            'custom_meal': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Or enter custom meal name'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Add notes or modifications...'
            }),
        }
    
    def clean(self):
        """Validate that either recipe or custom_meal is provided"""
        cleaned_data = super().clean()
        recipe = cleaned_data.get('recipe')
        custom_meal = cleaned_data.get('custom_meal')
        
        if not recipe and not custom_meal:
            raise forms.ValidationError(
                "Please either select a recipe or enter a custom meal name."
            )
        
        return cleaned_data


class CustomRecipeForm(forms.ModelForm):
    """Form for creating custom recipes"""
    
    class Meta:
        model = Recipe
        fields = ['name', 'description', 'ingredients', 'instructions', 'prep_time', 'cook_time', 'servings', 'meal_type']  # REMOVED 'category'
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Recipe name (e.g., Grandma\'s Cookies)'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': 'Brief description of the recipe'
            }),
            'ingredients': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'List ingredients, one per line:\n- 2 cups flour\n- 1 cup sugar\n- etc.'
            }),
            'instructions': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Step-by-step cooking instructions'
            }),
            'prep_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Minutes'
            }),
            'cook_time': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Minutes'
            }),
            'servings': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Number of servings'
            }),
        }

class WeeklyMealForm(forms.Form):
    """Form for a single meal in weekly planner"""
    
    date = forms.DateField(widget=forms.HiddenInput())
    meal_type = forms.CharField(widget=forms.HiddenInput())
    recipe = forms.ModelChoiceField(
        queryset=Recipe.objects.all(),
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control form-select',
        }),
        empty_label="Select a recipe..."
    )
    custom_meal = forms.CharField(
        required=False,
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Or enter custom meal'
        })
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 1,
            'placeholder': 'Notes...'
        })
    )


class BaseWeeklyMealPlanFormSet(BaseFormSet):
    """Custom formset for weekly meal planning"""
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.dates = kwargs.pop('dates', [])
        super().__init__(*args, **kwargs)
    
    def _construct_forms(self):
        """Construct forms for each date and meal type"""
        self.forms = []
        meal_types = ['breakfast', 'lunch', 'dinner', 'midnight_snack']
        
        for date in self.dates:
            for meal_type in meal_types:
                # Try to get existing meal plan
                existing_meal = None
                if self.user:
                    existing_meal = MealPlan.objects.filter(
                        user=self.user,
                        date=date,
                        meal_type=meal_type
                    ).first()
                
                # Prepare initial data
                initial = {
                    'date': date,
                    'meal_type': meal_type,
                }
                
                if existing_meal:
                    initial.update({
                        'recipe': existing_meal.recipe,
                        'custom_meal': existing_meal.custom_meal,
                        'notes': existing_meal.notes,
                    })
                
                # Create form with prefix for unique field names
                form = WeeklyMealForm(
                    initial=initial,
                    prefix=f'{date.isoformat()}_{meal_type}'
                )
                self.forms.append(form)
    
    def is_valid(self):
        """Validate all forms - FIXED VERSION"""
        if not self.is_bound:
            return False
        
        forms_valid = True
        for i, form in enumerate(self.forms):
            # Manually bind data to each form
            form_data = {}
            prefix = form.prefix
            
            for field_name in ['date', 'meal_type', 'recipe', 'custom_meal', 'notes']:
                key = f'{prefix}-{field_name}'
                if key in self.data:
                    form_data[key] = self.data[key]
            
            # Create a new form instance with the data
            self.forms[i] = WeeklyMealForm(
                data=form_data if form_data else None,
                initial=form.initial,
                prefix=prefix
            )
            
            if not self.forms[i].is_valid():
                forms_valid = False
        
        return forms_valid
    
    def save(self):
        """Save all forms in the formset - IMPROVED VERSION"""
        saved_count = 0
        deleted_count = 0
        
        for form in self.forms:
            if form.is_valid():
                date = form.cleaned_data.get('date')
                meal_type = form.cleaned_data.get('meal_type')
                recipe = form.cleaned_data.get('recipe')
                custom_meal = form.cleaned_data.get('custom_meal', '').strip()
                notes = form.cleaned_data.get('notes', '').strip()
                
                if not date or not meal_type:
                    continue
                
                # If both recipe and custom_meal are empty, delete the meal plan
                if not recipe and not custom_meal:
                    deleted = MealPlan.objects.filter(
                        user=self.user,
                        date=date,
                        meal_type=meal_type
                    ).delete()
                    if deleted[0] > 0:
                        deleted_count += deleted[0]
                else:
                    # Create or update meal plan
                    meal_plan, created = MealPlan.objects.update_or_create(
                        user=self.user,
                        date=date,
                        meal_type=meal_type,
                        defaults={
                            'recipe': recipe,
                            'custom_meal': custom_meal,
                            'notes': notes,
                        }
                    )
                    saved_count += 1
        
        return {
            'saved': saved_count,
            'deleted': deleted_count
        }


def WeeklyMealPlanFormSet(data=None, user=None, dates=None):
    """Factory function to create weekly meal plan formset"""
    if dates is None:
        dates = []
    
    meal_types = ['breakfast', 'lunch', 'dinner', 'midnight_snack']
    extra = len(dates) * len(meal_types)
    
    FormSet = formset_factory(
        WeeklyMealForm,
        formset=BaseWeeklyMealPlanFormSet,
        extra=0,
        max_num=extra
    )
    
    return FormSet(data, user=user, dates=dates)


class CommentForm(forms.ModelForm):
    """Form for creating/editing comments"""
    
    class Meta:
        model = Comment
        fields = ['content', 'is_important']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Add important information about allergies, preferences, meal planning tips, or reminders...'
            }),
            'is_important': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
                'checked': True
            }),
        }
        labels = {
            'content': 'Note Content',
            'is_important': 'Mark as important'
        }


class UserProfileForm(forms.ModelForm):
    """Form for editing user profile"""
    
    class Meta:
        model = UserProfile
        fields = ['allergies', 'preferences']
        widgets = {
            'allergies': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'List your food allergies separated by commas (e.g., peanuts, shellfish, dairy, gluten)'
            }),
            'preferences': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'List your dietary preferences (e.g., vegetarian, vegan, low-carb, gluten-free, keto)'
            }),
        }
        labels = {
            'allergies': 'Food Allergies',
            'preferences': 'Dietary Preferences',
        }
        help_texts = {
            'allergies': 'Important: List any foods you are allergic to',
            'preferences': 'Optional: Your dietary preferences and restrictions',
        }

class UserUpdateForm(forms.ModelForm):
    """Form for updating username and email"""
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Username'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Email address'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First name (optional)'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last name (optional)'
            }),
        }
        help_texts = {
            'username': '150 characters or fewer. Letters, digits and @/./+/-/_ only.',
        }


class CustomPasswordChangeForm(PasswordChangeForm):
    """Custom password change form with Bootstrap styling"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Current password'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'New password'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm new password'
        })
