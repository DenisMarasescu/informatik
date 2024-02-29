from django.contrib import admin

from accounts.models import Homework, MCQResult, MultipleChoiceProblem, Problem, Solution

# Register your models here.

admin.site.register(Homework)
admin.site.register(Problem)
admin.site.register(Solution)
admin.site.register(MultipleChoiceProblem)
admin.site.register(MCQResult)