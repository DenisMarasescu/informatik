from django.contrib import admin
from .models import User

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('email', 'first_name', 'last_name', 'is_profesor', 'school', 'id')
    filter_horizontal = ('badges',)
    # add other fields as needed