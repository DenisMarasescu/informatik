import uuid
from django import forms

from accounts.models import Course, MultipleChoiceProblem, Solution

class ProblemGenerationForm(forms.Form):
    THEME_CHOICES = [
        ('doubly_linked_lists', 'Doubly Linked Lists'),
        ('searching_algorithms', 'Searching Algorithms'),
        ('sorting_algorithms', 'Sorting Algorithms'),
        ('graph_algorithms', 'Graph Algorithms'),
        ('dynamic_programming', 'Dynamic Programming'),
        ('recursion_backtracking', 'Recursion and Backtracking'),
        ('data_structures', 'Data Structures'),
        ('trees', 'Trees and Tree Algorithms'),
        ('string_processing', 'String Processing'),
        ('computational_geometry', 'Computational Geometry'),
    ]
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]

    NUM_PROBLEMS_CHOICES = [(i, str(i)) for i in range(1, 11)]  # Example: Up to 10 problems

    theme = forms.ChoiceField(choices=THEME_CHOICES, label="Theme")
    min_difficulty = forms.ChoiceField(choices=DIFFICULTY_CHOICES, label="Minimum Difficulty", required=False)
    max_difficulty = forms.ChoiceField(choices=DIFFICULTY_CHOICES, label="Maximum Difficulty", required=False)
    num_problems = forms.ChoiceField(choices=NUM_PROBLEMS_CHOICES, label="Number of Problems", required=False)
    generate_full_subject = forms.BooleanField(required=False, help_text="Generate an entire subject.")


class SingleDifficultyProblemGenerationForm(forms.Form):
    THEME_CHOICES = [
        ('doubly_linked_lists', 'Liste dublu înlănțuite'),
        ('searching_algorithms', 'Algoritmi de căutare'),
        ('sorting_algorithms', 'Algoritmi de sortare'),
        ('graph_algorithms', 'Algoritmi pe grafuri'),
        ('dynamic_programming', 'Programare dinamică'),
        ('recursion_backtracking', 'Recursivitate și backtracking'),
        ('data_structures', 'Structuri de date'),
        ('trees', 'Arbori și algoritmi pe arbori'),
        ('string_processing', 'Procesarea șirurilor'),
        ('computational_geometry', 'Geometrie computațională'),
    ]
    DIFFICULTY_CHOICES = [
        ('easy', 'Usor'),
        ('medium', 'Mediu'),
        ('hard', 'Greu'),
    ]
    NUM_PROBLEMS_CHOICES = [(i, str(i)) for i in range(1, 11)]

    theme = forms.ChoiceField(choices=THEME_CHOICES, label="Theme")
    difficulty = forms.ChoiceField(choices=DIFFICULTY_CHOICES, label="Difficulty")
    num_problems = forms.ChoiceField(choices=NUM_PROBLEMS_CHOICES, label="Number of Problems", required=False)
    generate_full_subject = forms.BooleanField(required=False, help_text="Generate an entire subject.")


class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['name', 'description']

    def save(self, commit=True):
        course = super().save(commit=False)
        # Ensure the entrance code is unique
        while True:
            entrance_code = str(uuid.uuid4())[:8]  # Generate a random code
            if not Course.objects.filter(entrance_code=entrance_code).exists():
                break
        course.entrance_code = entrance_code
        if commit:
            course.save()
            self._save_m2m()
        return course
    


class HomeworkCreationForm(forms.Form):
    THEME_CHOICES = [
        ('doubly_linked_lists', 'Doubly Linked Lists'),
        ('searching_algorithms', 'Searching Algorithms'),
        ('sorting_algorithms', 'Sorting Algorithms'),
        ('graph_algorithms', 'Graph Algorithms'),
        ('dynamic_programming', 'Dynamic Programming'),
        ('recursion_backtracking', 'Recursion and Backtracking'),
        ('data_structures', 'Data Structures'),
        ('trees', 'Trees and Tree Algorithms'),
        ('string_processing', 'String Processing'),
        ('computational_geometry', 'Computational Geometry'),
    ]

    num_problems = forms.IntegerField(label='Number of Problems', min_value=1, initial=5)
    min_difficulty = forms.ChoiceField(choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')], label="Minimum Difficulty")
    max_difficulty = forms.ChoiceField(choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')], label="Maximum Difficulty")
    themes = forms.MultipleChoiceField(choices=THEME_CHOICES, label="Themes", widget=forms.CheckboxSelectMultiple(), required=False)
    deadline = forms.DateTimeField(label='Deadline', widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}), help_text='Please use the format: YYYY-MM-DD HH:MM')




class SolutionForm(forms.ModelForm):
    class Meta:
        model = Solution
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'cols': 80, 'rows': 20}),
        }
        labels = {
            'text': 'Your Solution',
        }


class MultipleChoiceProblemForm(forms.ModelForm):
    class Meta:
        model = MultipleChoiceProblem
        fields = ['question', 'choices', 'correct_answer']
        widgets = {
            'choices': forms.Textarea(attrs={'placeholder': '{"A": "Option 1", "B": "Option 2", "C": "Option 3"}'}),
        }

class TestCreationForm(forms.Form):

    TOPIC_CHOICES = [
        ('doubly_linked_lists', 'Doubly Linked Lists'),
        ('searching_algorithms', 'Searching Algorithms'),
        ('sorting_algorithms', 'Sorting Algorithms'),
        ('graph_algorithms', 'Graph Algorithms'),
        ('dynamic_programming', 'Dynamic Programming'),
        ('recursion_backtracking', 'Recursion and Backtracking'),
        ('data_structures', 'Data Structures'),
        ('trees', 'Trees and Tree Algorithms'),
        ('string_processing', 'String Processing'),
        ('computational_geometry', 'Computational Geometry'),
    ]

    title = forms.CharField(max_length=100)
    topic = forms.MultipleChoiceField(choices=TOPIC_CHOICES, widget=forms.CheckboxSelectMultiple)
    difficulty = forms.ChoiceField(choices=[('easy', 'Easy'), ('medium', 'Medium'), ('hard', 'Hard')])
    number_of_problems = forms.IntegerField(min_value=1, initial=5, max_value=15)  # Add this field
    # questions = forms.ModelMultipleChoiceField(queryset=MultipleChoiceProblem.objects.none(), widget=forms.CheckboxSelectMultiple, required=False)
    deadline = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        required=True  # or False if you want to make it optional
    )

    def __init__(self, *args, **kwargs):
        super(TestCreationForm, self).__init__(*args, **kwargs)
        # self.fields['questions'].queryset = MultipleChoiceProblem.objects.all()