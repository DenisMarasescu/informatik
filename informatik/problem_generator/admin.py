from django.contrib import admin

from accounts.models import Homework, MCQResult, MultipleChoiceProblem, Problem, Solution, Message, Badge

# Register your models here.

admin.site.register(Homework)
admin.site.register(Problem)
admin.site.register(Solution)
admin.site.register(MultipleChoiceProblem)
admin.site.register(MCQResult)
admin.site.register(Message)
@admin.register(Badge)
class BadgeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description', 'criteria')